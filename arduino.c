
#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdint.h>

#define MOSFET_BIT PB0
#define ADC_CS_BIT PB2

#define SAMPLES 16
#define FRAME_SIZE 32

volatile uint8_t wave[2][FRAME_SIZE];
volatile uint8_t ready[2] = {0, 0};

volatile uint8_t sampleBuf = 0;
volatile uint8_t sampleIndex = 0;
volatile uint8_t samplePhase = 0;

volatile uint8_t txBuf = 0;
volatile uint8_t txIndex = 0;
volatile uint8_t txActive = 0;

static inline uint16_t adcRead12()
{
    uint8_t hi, lo;

    PORTB &= ~_BV(ADC_CS_BIT);

    SPDR = 0;
    while (!(SPSR & _BV(SPIF)));
    hi = SPDR;

    SPDR = 0;
    while (!(SPSR & _BV(SPIF)));
    lo = SPDR;

    PORTB |= _BV(ADC_CS_BIT);

    uint16_t raw = ((uint16_t)hi << 8) | lo;
    return (raw >> 1) & 0x0FFF;
}

static inline void storeSample(uint8_t index, uint16_t adc)
{
    uint16_t packed =
        ((uint16_t)(index & 0x0F) << 12) | adc;

    wave[sampleBuf][index * 2] = packed >> 8;
    wave[sampleBuf][index * 2 + 1] = packed & 0xFF;
}

static inline void startTransmission()
{
    uint8_t candidate = sampleBuf ^ 1;

    if (!txActive && ready[candidate])
    {
        txBuf = candidate;
        ready[candidate] = 0;
        txIndex = 0;
        txActive = 1;

        UCSR0B |= _BV(UDRIE0);
    }
}

ISR(TIMER2_COMPA_vect)
{
    uint16_t adc = adcRead12();

    uint8_t i = sampleIndex;
    storeSample(i, adc);

    sampleIndex++;

    if (sampleIndex >= SAMPLES)
    {
        ready[sampleBuf] = 1;
        TIMSK2 &= ~_BV(OCIE2A);
    }
}

ISR(TIMER1_COMPB_vect)
{
    PORTB |= _BV(MOSFET_BIT);
}

ISR(TIMER1_COMPA_vect)
{
    PORTB &= ~_BV(MOSFET_BIT);

    sampleBuf ^= 1;
    sampleIndex = 0;

    TIFR2 = _BV(OCF2A);

    if (samplePhase == 0)
    {
        TCNT2 = 0;
        TIMSK2 |= _BV(OCIE2A);

        storeSample(0, adcRead12());
        sampleIndex = 1;

        samplePhase = 1;
    }
    else
    {
        TCNT2 = 10;
        TIMSK2 |= _BV(OCIE2A);

        samplePhase = 0;
    }

    startTransmission();
}

ISR(USART_UDRE_vect)
{
    if (txIndex >= FRAME_SIZE)
    {
        uint8_t next = txBuf ^ 1;

        if (ready[next])
        {
            txBuf = next;
            ready[next] = 0;
            txIndex = 0;
        }
        else
        {
            txActive = 0;
            UCSR0B &= ~_BV(UDRIE0);
            return;
        }
    }

    UDR0 = wave[txBuf][txIndex++];
}

void setup()
{
    cli();

    DDRB |= _BV(DDB0) | _BV(DDB2) |
            _BV(DDB3) | _BV(DDB5);

    DDRB &= ~_BV(DDB4);

    PORTB &= ~_BV(PB0);
    PORTB |= _BV(PB2);

    DDRD |= _BV(DDD7);
    PORTD &= ~_BV(PD7);

    SPCR = _BV(SPE) | _BV(MSTR);
    SPSR = 0;

    UCSR0A = 0;
    UBRR0H = 0;
    UBRR0L = 0;

    UCSR0C = _BV(UCSZ01) | _BV(UCSZ00);
    UCSR0B = _BV(TXEN0);

    TCCR1A = 0;
    TCCR1B = 0;

    TCNT1 = 0;

    OCR1A = 779;
    OCR1B = 699;

    TIFR1 = _BV(OCF1A) | _BV(OCF1B);
    TIMSK1 = _BV(OCIE1A) | _BV(OCIE1B);

    TCCR2A = _BV(WGM21);
    TCCR2B = 0;

    TCNT2 = 0;
    OCR2A = 19;

    TIFR2 = _BV(OCF2A);
    TIMSK2 = 0;

    TCCR1B = _BV(WGM12) | _BV(CS11);
    TCCR2B = _BV(CS21);

    sei();
}

void loop()
{
}
