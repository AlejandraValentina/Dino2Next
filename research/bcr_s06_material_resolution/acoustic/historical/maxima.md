# Máximos de los controles dirigidos VAL010

Todos los101instantes y las máscaras originales se conservan. Valores centrales y cotas de referencia se distinguen; los datos completos están en maxima-and-all-samples.json. No es aceptación de la batería.

| N / CFL | Componente | Máximo seleccionado | j / t(s) | abs(Cref)/A0 | abs(C-Cref)/A0 | Error amplitud relativo (cota) | Fase central(rad) |
|---|---|---|---|---|---|---|---|
| 200/0.2 | incident | absolute_error_upper_over_A0 | 74 / 0.6254141485 | 0.6200016223 | 0.01562658781 | 0.02479282014 | 0.004593485276 |
| 200/0.2 | incident | relative_amplitude_error_upper | 83 / 0.7014780314 | 0.01209130801 | 0.004070212926 | 0.3364537242 | 0.009729338302 |
| 200/0.2 | incident | phase_error_upper | 81 / 0.6845749463 | 0.04581099651 | 0.006648978059 | 0.1447408373 | 0.01009851689 |
| 200/0.2 | reflected | absolute_error_upper_over_A0 | 74 / 0.6254141485 | 0.3953528852 | 0.01554501269 | 0.0389247469 | -0.005454425388 |
| 200/0.2 | reflected | relative_amplitude_error_upper | 67 / 0.5662533507 | 0.01209130801 | 0.006048368908 | 0.4994322271 | -0.04030067857 |
| 200/0.2 | reflected | phase_error_upper | 67 / 0.5662533507 | 0.01209130801 | 0.006048368908 | 0.4994322271 | -0.04030067857 |
| 200/0.2 | pressure | absolute_error_upper_over_A0 | 74 / 0.6254141485 | 0.22578033 | 0.03117108103 | No definida | 0.04159507771 |
| 400/0.2 | incident | absolute_error_upper_over_A0 | 75 / 0.633865691 | 0.5079181356 | 0.00403288591 | 0.007800817887 | 0.001486235374 |
| 400/0.2 | incident | relative_amplitude_error_upper | 83 / 0.7014780314 | 0.01209138367 | 0.001191077113 | 0.09843295782 | 0.003649101033 |
| 400/0.2 | incident | phase_error_upper | 83 / 0.7014780314 | 0.01209138367 | 0.001191077113 | 0.09843295782 | 0.003649101033 |
| 400/0.2 | reflected | absolute_error_upper_over_A0 | 75 / 0.633865691 | 0.5079181356 | 0.004026917189 | 0.007853775186 | -0.001080278689 |
| 400/0.2 | reflected | relative_amplitude_error_upper | 67 / 0.5662533507 | 0.01209138367 | 0.001266653697 | 0.1046047132 | -0.00598057809 |
| 400/0.2 | reflected | phase_error_upper | 67 / 0.5662533507 | 0.01209138367 | 0.001266653697 | 0.1046047132 | -0.00598057809 |
| 400/0.2 | pressure | absolute_error_upper_over_A0 | 75 / 0.633865691 | 0 | 0.008057379817 | No definida | No definida |
| 800/0.05 | incident | absolute_error_upper_over_A0 | 75 / 0.633865691 | 0.5079209727 | 0.0009844393788 | 0.001910483663 | 0.0003267732875 |
| 800/0.05 | incident | relative_amplitude_error_upper | 83 / 0.7014780314 | 0.01209140234 | 0.0002982569091 | 0.02464359943 | 0.001059249511 |
| 800/0.05 | incident | phase_error_upper | 83 / 0.7014780314 | 0.01209140234 | 0.0002982569091 | 0.02464359943 | 0.001059249511 |
| 800/0.05 | reflected | absolute_error_upper_over_A0 | 75 / 0.633865691 | 0.5079209727 | 0.0009780555559 | 0.001905057121 | -0.0002803037988 |
| 800/0.05 | reflected | relative_amplitude_error_upper | 67 / 0.5662533507 | 0.01209140234 | 0.0002758032393 | 0.02277972135 | -0.001186932059 |
| 800/0.05 | reflected | phase_error_upper | 67 / 0.5662533507 | 0.01209140234 | 0.0002758032393 | 0.02277972135 | -0.001186932059 |
| 800/0.05 | pressure | absolute_error_upper_over_A0 | 75 / 0.633865691 | 0 | 0.001962368364 | No definida | No definida |

La presión total en j75 tiene referencia analíticamente nula: no se calcula fase ni error relativo; permanece el gate absoluto. Fuera de máscara, el JSON conserva las muestras y distingue fase no evaluada contractualmente de referencia matemáticamente nula.
