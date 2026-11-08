// El else se asocia al if más cercano (resolución del conflicto LL(1) en 'sino')
int a = 1;
int b = 0;
if (a > 0) if (b > 0) printf(1); else printf(2);
