#include <Arduino.h>
#include <avr/io.h>
#include <avr/interrupt.h>

#if F_CPU != 16000000UL
#error "This code requires a 16MHz Arduino Uno"
#endif
#define MOSFET_BIT PB0

#define ON_TICKS       640
#define PERIOD_TICKS   3840
#define SAMPLE_STEP    80
#define SAMPLE_COUNT   16
#define ADC_SAMPLE_DELAY_TICKS  259
#define MOSFET_OFF_OFFSET_TICKS 0
#define SAMPLE_START (ON_TICKS + MOSFET_OFF_OFFSET_TICKS - ADC_SAMPLE_DELAY_TICKS)
#define TIMER2_PRESCALER 8
#define TIMER2_COUNTS    (ON_TICKS / TIMER2_PRESCALER)

volatile uint16_t samples[SAMPLE_COUNT];
volatile uint8_t sampleIndex = 0;
volatile uint8_t blockReady = 0;
ISR(TIMER1_COMPA_vect)
{
    PORTB |= _BV(MOSFET_BIT);
    TCNT2 = 0;
    GTCCR |= _BV(PSRASY);
    TIFR2 = _BV(OCF2A);
    TIMSK2 |= _BV(OCIE2A);
}
ISR(TIMER2_COMPA_vect)
{
    PORTB &= ~_BV(MOSFET_BIT);
    TIMSK2 &= ~_BV(OCIE2A);
}
ISR(ADC_vect)
{
    TIFR1 = _BV(OCF1B);
    uint8_t index = sampleIndex;
    uint16_t value = ADC & 0x03FF;
    samples[index] = ((uint16_t)index << 12) | value;
    if (index == SAMPLE_COUNT - 1)
    {
        sampleIndex = 0;
        blockReady = 1;
        OCR1B = SAMPLE_START;
    }
    else
    {
        sampleIndex = index + 1;
        OCR1B = SAMPLE_START + (sampleIndex * SAMPLE_STEP);
    }
}
void setup()
{
    cli();
    DDRB |= _BV(MOSFET_BIT);
    PORTB &= ~_BV(MOSFET_BIT);
    Serial.begin(1000000);
    TIMSK0 = 0;
    TCCR1A = 0;
    TCCR1B = 0;
    TIMSK1 = 0;
    OCR1A = PERIOD_TICKS - 1;
    OCR1B = SAMPLE_START;
    TCCR2A = _BV(WGM21);
    TCCR2B = _BV(CS21);
    OCR2A = TIMER2_COUNTS - 1;
    TCNT2 = 0;
    TIFR2 = _BV(OCF2A);
    TIMSK2 = 0;
    ADMUX = _BV(REFS0);
    DIDR0 |= _BV(ADC0D);
    ADCSRB = 0;
    ADCSRA =
        _BV(ADEN)  |
        _BV(ADPS2) |
        _BV(ADPS1) |
        _BV(ADPS0);
    ADCSRA |= _BV(ADSC);
    while (ADCSRA & _BV(ADSC))
    {
    }
    uint16_t discard = ADC;
    (void)discard;
    ADCSRA |= _BV(ADIF);
    ADCSRB = _BV(ADTS2) | _BV(ADTS0);
    ADCSRA =
        _BV(ADEN)  |
        _BV(ADATE) |
        _BV(ADIE)  |
        _BV(ADPS2) |
        _BV(ADPS1) |
        _BV(ADPS0);
    TIFR1 =
        _BV(OCF1A) |
        _BV(OCF1B) |
        _BV(TOV1);
    TCNT1 = OCR1A - 1;
    TIMSK1 = _BV(OCIE1A);
    TCCR1B = _BV(WGM12) | _BV(CS10);
    sei();
}
void loop()
{
    uint16_t buffer[SAMPLE_COUNT];
    uint8_t ready = 0;
    uint8_t oldSREG = SREG;
    cli();
    if (blockReady)
    {
        for (uint8_t i = 0; i < SAMPLE_COUNT; i++)
        {
            buffer[i] = samples[i];
        }
        blockReady = 0;
        ready = 1;
    }
    SREG = oldSREG;
    if (ready)
    {
        for (uint8_t i = 0; i < SAMPLE_COUNT; i++)
        {
            Serial.write((uint8_t)(buffer[i] & 0xFF));
            Serial.write((uint8_t)(buffer[i] >> 8));
        }
    }
}