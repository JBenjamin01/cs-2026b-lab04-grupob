# Comparaciones — Laboratorio 06

## 1\. Secuencia UML (Lab 05) frente a vista dinámica C4 (E4)

La secuencia UML de «confirmar y pagar» muestra a nivel de clases las 10 líneas de vida, las
operaciones exactas (`confirmarYPagar()`, `reservar()`, `registrarPago()`…), los fragmentos
`alt` y `loop`, la rama de rechazo o expiración del pago y el estado de cada objeto. La vista
dinámica solo muestra la secuencia numerada de los pasos del camino feliz entre contenedores y
componentes, con el protocolo de cada paso, y omite ramas, bucles y clases. La secuencia UML sirve
a los developers que implementan y prueban el flujo; la vista dinámica sirve al equipo técnico y
a operaciones, y a quien necesita entender quién habla con quién sin leer el código.

## 2\. Diagrama escrito a mano (C4-PlantUML) frente a modelo exportado (Structurizr DSL) (E6)

|Aspecto|Escrito a mano (`contexto-manual.puml`)|Exportado de `workspace.dsl`|
|-|-|-|
|Tiempo invertido|Compilar el diagrama manual tomó 2,4 s (1 vista). Escribirlo desde cero se estima en unos 15 a 20 min|5,0 s para exportar y generar las 5 vistas (medido con Measure-Command)|
|Errores encontrados|Ninguno al compilar; el riesgo es que el nombre de un elemento quede distinto al del DSL|Ninguno: validate devolvió código 0 y se generaron 5 .puml, 5 .mmd y 5 PNG||Si mañana cambia el nombre de un contenedor|Hay que corregirlo en cada archivo `.puml` o `.mmd` donde aparezca; es fácil olvidar alguno|Se cambia una vez en `workspace.dsl` y se vuelve a exportar; todas las vistas quedan coherentes|

Conclusión: para un solo diagrama pequeño, escribir a mano es rápido; para varias vistas que
deben mantenerse coherentes con un monolito que evoluciona, conviene modelar una sola vez.

