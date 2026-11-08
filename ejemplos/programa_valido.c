// Programa válido de MiniC: suma de los números del 1 al n y paridad
int n = 10;
int suma = 0;
int i = 1;
float promedio;
while (i <= n) {
    suma = suma + i;
    i = i + 1;
}
promedio = suma / n;
if (suma > 50) {
    printf(suma);
} else {
    printf(0);
}
// expresión con precedencia y paréntesis
int r = -(2 + 3) * 4 - 6 / 2;
printf(r);
