# BASE Wave-to-Wave Repeatability Analysis

## Overview

This analysis compares each ADC sample with the corresponding sample recorded 13 waveforms earlier.  
The comparison is performed across the entire `BASE.bin` dataset to evaluate the repeatability of the signal pattern.

---

## Measurement Metrics

- **Mean Error:** The average absolute difference between corresponding samples separated by 13 waveforms.
- **Max Error:** The maximum absolute difference observed for each sample position.

The absolute difference is calculated as:

```text
Error = abs(Current_Sample - Previous_Sample)

All measurements are converted to a signed integer type before subtraction to prevent unsigned integer overflow.

---

## Results

The results demonstrate excellent waveform repeatability:

- Samples 1, 2, 3, and 6 have zero error across all comparisons.
- Sample 4 has a mean error of only 0.810 ADC counts, with a maximum error of 4 counts.
- Samples 7–16 have mean errors ranging from 0.501 to 0.689 ADC counts.
- The maximum error across all remaining sample positions does not exceed 3 ADC counts, except for sample 4, which reaches 4 counts.
- Sample 5 has a mean error of 0.093 ADC counts and a maximum error of 2 counts.

### Error Summary

| Sample | Mean Error | Max Error |
|---:|---:|---:|
| 1 | 0.000 | 0 |
| 2 | 0.000 | 0 |
| 3 | 0.000 | 0 |
| 4 | 0.810 | 4 |
| 5 | 0.093 | 2 |
| 6 | 0.000 | 0 |
| 7 | 0.662 | 3 |
| 8 | 0.501 | 2 |
| 9 | 0.572 | 2 |
| 10 | 0.678 | 3 |
| 11 | 0.523 | 2 |
| 12 | 0.618 | 3 |
| 13 | 0.689 | 2 |
| 14 | 0.564 | 2 |
| 15 | 0.555 | 2 |
| 16 | 0.621 | 2 |

---

## Conclusion

The comparison confirms that the baseline waveform pattern repeats consistently every 13 waveforms.

The mean absolute error remains below 1 ADC count for every sample position, while the maximum observed 
difference is only 4 ADC counts.

These results indicate that the acquisition system provides highly repeatable baseline measurements, 
making the recorded data suitable for use as a reference during subsequent signal analysis and metal-detection experiments.
```