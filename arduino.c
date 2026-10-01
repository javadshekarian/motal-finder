#include <avr/io.h>

#define TX_BIT PB0

#define PHASES 201
#define STEP_CYCLES 8
#define TX_CYCLES 160

static inline void delay_cycles(uint16_t cycles)
{
    while (cycles--)
        __asm__ __volatile__("nop");
}

static inline uint16_t adc_read()
{
    ADCSRA |= (1 << ADSC);

    while (ADCSRA & (1 << ADSC));

    return ADC;
}

void setup()
{
    DDRB |= (1 << TX_BIT);
    PORTB &= ~(1 << TX_BIT);

    ADMUX = (1 << REFS0);

    ADCSRA =
        (1 << ADEN) |
        (1 << ADPS1) |
        (1 << ADPS0);

    ADCSRB = 0;

    DIDR0 = (1 << ADC0D);

    Serial.begin(1000000);

    adc_read();
}

void loop()
{
    PORTB |= (1 << TX_BIT);

    delay_cycles(TX_CYCLES);

    PORTB &= ~(1 << TX_BIT);

    for (uint16_t phase = 1; phase <= PHASES; phase++)
    {
        uint16_t value = adc_read();

        Serial.write((uint8_t)(value & 0xFF));
        Serial.write((uint8_t)(value >> 8));
        Serial.write((uint8_t)phase);

        if (phase < PHASES)
            delay_cycles(STEP_CYCLES);
    }
}
