int n = 10;
int suma = 0;
float promedio;
while (n > 0) {
    suma = suma + n;
    n = n - 1;
}
if (suma >= 50) {
    promedio = suma / 10;
} else {
    promedio = 0;
}
