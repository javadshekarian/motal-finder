#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <poll.h>
#include <pty.h>
#include <termios.h>
#include <unistd.h>
#include <vector>

static constexpr const char* SERIAL_DEVICE = "/dev/ttyACM0";
static constexpr const char* PROXY_LINK = "/tmp/arduino-proxy";
static constexpr std::size_t FRAME_SIZE = 32;
#define ADD_COUNTER 1
static volatile sig_atomic_t stopRequested = 0;

static void handleSignal(int)
{
    stopRequested = 1;
}

static bool configureSerial(int fd)
{
    termios tty{};
    if (tcgetattr(fd, &tty) != 0)
        return false;

    cfmakeraw(&tty);
    if (cfsetispeed(&tty, B1000000) != 0 || cfsetospeed(&tty, B1000000) != 0)
        return false;

    tty.c_cflag &= ~(PARENB | CSTOPB | CSIZE);
    tty.c_cflag |= CS8 | CLOCAL | CREAD;
#ifdef CRTSCTS
    tty.c_cflag &= ~CRTSCTS;
#endif
    tty.c_iflag &= ~(IXON | IXOFF | IXANY);
    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 0;

    return tcsetattr(fd, TCSANOW, &tty) == 0;
}

static bool setRawPty(int fd)
{
    termios tty{};
    if (tcgetattr(fd, &tty) != 0)
        return false;

    cfmakeraw(&tty);
    tty.c_cflag |= CLOCAL | CREAD;
    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 0;
    return tcsetattr(fd, TCSANOW, &tty) == 0;
}

static bool setNonBlocking(int fd)
{
    int flags = fcntl(fd, F_GETFL, 0);
    return flags >= 0 && fcntl(fd, F_SETFL, flags | O_NONBLOCK) == 0;
}

static uint16_t readWord(const uint8_t* frame, uint8_t index)
{
    return static_cast<uint16_t>(frame[index * 2]) |
           (static_cast<uint16_t>(frame[index * 2 + 1]) << 8);
}

static void writeWord(uint8_t* frame, uint8_t index, uint16_t word)
{
    frame[index * 2] = static_cast<uint8_t>(word & 0xFF);
    frame[index * 2 + 1] = static_cast<uint8_t>(word >> 8);
}

static bool validFrame(const uint8_t* frame)
{
    for (uint8_t i = 0; i < 16; ++i)
    {
        uint16_t word = readWord(frame, i);
        if ((word >> 12) != i)
            return false;
        if (i != 1 && i != 2 && (word & 0x0C00))
            return false;
    }
    return true;
}

static bool writeAll(int fd, const uint8_t* data, std::size_t length)
{
    std::size_t sent = 0;
    while (sent < length && !stopRequested)
    {
        ssize_t n = write(fd, data + sent, length - sent);
        if (n > 0)
        {
            sent += static_cast<std::size_t>(n);
            continue;
        }
        if (n < 0 && errno == EINTR)
            continue;
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK))
        {
            pollfd pfd{fd, POLLOUT, 0};
            int result = poll(&pfd, 1, -1);
            if (result < 0 && errno == EINTR)
                continue;
            if (result <= 0 || (pfd.revents & (POLLERR | POLLHUP | POLLNVAL)))
                return false;
            continue;
        }
        return false;
    }
    return sent == length;
}

int main()
{
    std::signal(SIGINT, handleSignal);
    std::signal(SIGTERM, handleSignal);

    int serialFd = open(SERIAL_DEVICE, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (serialFd < 0)
    {
        std::perror("Cannot open Arduino serial port");
        return 1;
    }

    if (!configureSerial(serialFd))
    {
        std::perror("Cannot configure Arduino serial port");
        close(serialFd);
        return 1;
    }

    std::fprintf(stderr, "Waiting 2 seconds for Arduino startup...\n");
    const auto warmupEnd = std::chrono::steady_clock::now() + std::chrono::seconds(2);
    uint8_t discardBuffer[512];

    while (!stopRequested && std::chrono::steady_clock::now() < warmupEnd)
    {
        pollfd pfd{serialFd, POLLIN, 0};
        int result = poll(&pfd, 1, 50);
        if (result < 0 && errno == EINTR)
            continue;

        if (result > 0 && (pfd.revents & POLLIN))
        {
            while (read(serialFd, discardBuffer, sizeof(discardBuffer)) > 0)
            {
            }
        }
    }

    if (stopRequested)
    {
        close(serialFd);
        return 0;
    }

    tcflush(serialFd, TCIFLUSH);

    int ptyMaster = -1;
    int ptySlave = -1;
    char slaveName[128]{};

    if (openpty(&ptyMaster, &ptySlave, slaveName, nullptr, nullptr) != 0)
    {
        std::perror("openpty failed");
        close(serialFd);
        return 1;
    }

    if (!setRawPty(ptySlave) || !setNonBlocking(ptyMaster))
    {
        std::perror("Cannot configure virtual serial port");
        close(ptySlave);
        close(ptyMaster);
        close(serialFd);
        return 1;
    }

    if (unlink(PROXY_LINK) != 0 && errno != ENOENT)
    {
        std::perror("Cannot remove old proxy link");
        close(ptySlave);
        close(ptyMaster);
        close(serialFd);
        return 1;
    }

    if (symlink(slaveName, PROXY_LINK) != 0)
    {
        std::perror("Cannot create proxy link");
        close(ptySlave);
        close(ptyMaster);
        close(serialFd);
        return 1;
    }

    std::fprintf(stderr, "Arduino input : %s\n", SERIAL_DEVICE);
    std::fprintf(stderr, "Python port   : %s -> %s\n", PROXY_LINK, slaveName);
#if ADD_COUNTER
    std::fprintf(stderr, "Counter       : enabled (0..12)\n");
#else
    std::fprintf(stderr, "Counter       : disabled (transparent frame forwarding)\n");
#endif
    std::fprintf(stderr, "Press Ctrl+C to stop.\n");

    std::vector<uint8_t> pending;
    uint8_t input[512];
    uint8_t counter = 0;
    uint64_t forwardedFrames = 0;

    while (!stopRequested)
    {
        pollfd pfd{serialFd, POLLIN, 0};
        int result = poll(&pfd, 1, 1000);
        if (result < 0)
        {
            if (errno == EINTR)
                continue;
            std::perror("Serial poll failed");
            break;
        }
        if (result == 0)
            continue;
        if (pfd.revents & (POLLERR | POLLHUP | POLLNVAL))
        {
            std::fprintf(stderr, "Arduino serial port disconnected.\n");
            break;
        }

        while (true)
        {
            ssize_t n = read(serialFd, input, sizeof(input));
            if (n > 0)
            {
                pending.insert(pending.end(), input, input + n);
                continue;
            }
            if (n < 0 && errno == EINTR)
            {
                if (stopRequested)
                    break;
                continue;
            }
            if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK))
                break;
            if (n == 0)
                break;
            std::perror("Serial read failed");
            goto cleanup;
        }

        while (pending.size() >= FRAME_SIZE)
        {
            if (!validFrame(pending.data()))
            {
                pending.erase(pending.begin());
                continue;
            }

            uint8_t frame[FRAME_SIZE];
            std::memcpy(frame, pending.data(), FRAME_SIZE);
            pending.erase(pending.begin(), pending.begin() + FRAME_SIZE);

#if ADD_COUNTER
            uint16_t word1 = readWord(frame, 1);
            word1 = static_cast<uint16_t>((word1 & ~0x0C00u) | ((counter & 0x03u) << 10));
            writeWord(frame, 1, word1);

            uint16_t word2 = readWord(frame, 2);
            word2 = static_cast<uint16_t>((word2 & ~0x0C00u) | (((counter >> 2) & 0x03u) << 10));
            writeWord(frame, 2, word2);
#endif

            if (!writeAll(ptyMaster, frame, FRAME_SIZE))
            {
                if (!stopRequested)
                    std::fprintf(stderr, "Cannot forward data to virtual serial port.\n");
                goto cleanup;
            }

            ++forwardedFrames;
#if ADD_COUNTER
            if (counter == 12)
                counter = 0;
            else
                ++counter;
#endif
        }
    }

cleanup:
    std::fprintf(stderr, "\nForwarded frames: %llu\n", static_cast<unsigned long long>(forwardedFrames));
    unlink(PROXY_LINK);
    close(ptySlave);
    close(ptyMaster);
    close(serialFd);
    return 0;
}