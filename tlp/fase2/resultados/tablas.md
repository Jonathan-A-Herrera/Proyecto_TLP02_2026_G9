# Resultados

## Métricas generales (48 oraciones)

| Enfoque | VP | VN | FP | FN | Precisión | Cobertura | Rechazo correcto | Exactitud | Errores de etiquetado | Fidelidad a L(G) |
|---|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 28 | 15 | 0 | 5 | 100.0 % | 84.8 % | 100.0 % | 89.6 % | 0 | 100.0 % |
| spaCy | 28 | 11 | 4 | 5 | 87.5 % | 84.8 % | 73.3 % | 81.2 % | 3 | 75.0 % |
| NLTK | 28 | 15 | 0 | 5 | 100.0 % | 84.8 % | 100.0 % | 89.6 % | 0 | 100.0 % |
| LLM zero-shot | 30 | 15 | 0 | 3 | 100.0 % | 90.9 % | 100.0 % | 93.8 % | 0 | 95.8 % |
| LLM few-shot | 30 | 15 | 0 | 3 | 100.0 % | 90.9 % | 100.0 % | 93.8 % | 0 | 95.8 % |

## Exactitud por nivel

| Enfoque | Nivel 1 | Nivel 2 | Nivel 3 |
|---|---|---|---|
| Parser propio | 100.0 % | 100.0 % | 68.8 % |
| spaCy | 81.2 % | 93.8 % | 68.8 % |
| NLTK | 100.0 % | 100.0 % | 68.8 % |
| LLM zero-shot | 100.0 % | 100.0 % | 81.2 % |
| LLM few-shot | 100.0 % | 100.0 % | 81.2 % |

## LLM frente a las reglas formales

| Variante | Correctas fuera de G aceptadas | Derivables en G rechazadas | Incorrectas aceptadas | Fidelidad a L(G) |
|---|---|---|---|---|
| LLM zero-shot | 2 de 5 | 0 de 28 | 0 de 15 | 95.8 % |
| LLM few-shot | 2 de 5 | 0 de 28 | 0 de 15 | 95.8 % |

## Detalle por oración (VP* = aceptada bien con error de etiquetado)

| id | nivel | oracion | esperado | en_gramatica | fenomeno | Parser propio | spaCy | NLTK | LLM zero-shot | LLM few-shot |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | El perro come | ACEPTA | SI | SVO mínimo, presente | VP | FN | VP | VP | VP |
| 2 | 1 | La niña duerme | ACEPTA | SI | sujeto femenino singular | VP | VP | VP | VP | VP |
| 3 | 1 | Los niños leen un libro | ACEPTA | SI | sujeto plural con objeto directo | VP | VP | VP | VP | VP |
| 4 | 1 | Las gatas comen | ACEPTA | SI | sujeto femenino plural | VP | FN | VP | VP | VP |
| 5 | 1 | Ana lee un libro | ACEPTA | SI | nombre propio como sujeto | VP | VP | VP | VP | VP |
| 6 | 1 | Luis vio el parque | ACEPTA | SI | pretérito con objeto | VP | VP | VP | VP | VP |
| 7 | 1 | El profesor lee un libro | ACEPTA | SI | sujeto masculino con objeto | VP | VP | VP | VP | VP |
| 8 | 1 | La profesora llegó | ACEPTA | SI | pretérito intransitivo | VP | VP | VP | VP | VP |
| 9 | 1 | Los perros ladran | ACEPTA | SI | plural intransitivo | VP | VP | VP | VP | VP |
| 10 | 1 | Pedro come | ACEPTA | SI | nombre propio intransitivo | VP | FN | VP | VP | VP |
| 11 | 1 | El niño está cansado | ACEPTA | SI | cópula con atributo | VP | VP | VP | VP | VP |
| 12 | 1 | Las niñas son altas | ACEPTA | SI | cópula con atributo plural | VP | VP | VP | VP | VP |
| 13 | 1 | La perro come | RECHAZA | NO | concordancia determinante-sustantivo | VN | VN | VN | VN | VN |
| 14 | 1 | Los niños come | RECHAZA | NO | concordancia sujeto-verbo | VN | VN | VN | VN | VN |
| 15 | 1 | Las niñas es altas | RECHAZA | NO | concordancia sujeto-cópula | VN | VN | VN | VN | VN |
| 16 | 1 | El niño están cansado | RECHAZA | NO | concordancia sujeto-cópula | VN | VN | VN | VN | VN |
| 17 | 2 | El perro negro come rápidamente | ACEPTA | SI | adjetivo y adverbio | VP | VP* | VP | VP | VP |
| 18 | 2 | Las niñas pequeñas leen un libro en la casa | ACEPTA | SI | adjetivo y frase preposicional | VP | VP | VP | VP | VP |
| 19 | 2 | La estudiante alta lee un libro | ACEPTA | SI | sustantivo de género común | VP | VP | VP | VP | VP |
| 20 | 2 | Los perros grandes ladraron ayer | ACEPTA | SI | adjetivo común, pretérito y adverbio | VP | VP | VP | VP | VP |
| 21 | 2 | El gato de la profesora duerme en la mesa | ACEPTA | SI | frase preposicional dentro del SN | VP | VP | VP | VP | VP |
| 22 | 2 | Ana vio el perro negro en el parque | ACEPTA | SI | objeto con adjetivo y frase preposicional | VP | VP | VP | VP | VP |
| 23 | 2 | La niña feliz come mucho | ACEPTA | SI | adjetivo común y adverbio | VP | VP | VP | VP | VP |
| 24 | 2 | Los estudiantes leyeron un libro sobre la mesa | ACEPTA | SI | pretérito y frase preposicional | VP | VP | VP | VP | VP |
| 25 | 2 | El perro que ladra come | ACEPTA | SI | relativa de sujeto | VP | VP* | VP | VP | VP |
| 26 | 2 | Luis dice que la niña duerme | ACEPTA | SI | subordinada sustantiva | VP | VP | VP | VP | VP |
| 27 | 2 | Las gatas negras están cansadas | ACEPTA | SI | adjetivo y atributo femenino plural | VP | VP | VP | VP | VP |
| 28 | 2 | Los gato negra come | RECHAZA | NO | concordancia dentro del SN | VN | VN | VN | VN | VN |
| 29 | 2 | La estudiante pequeño lee | RECHAZA | NO | género común mal concordado | VN | VN | VN | VN | VN |
| 30 | 2 | El perro que ladran come | RECHAZA | NO | concordancia dentro de la relativa | VN | VN | VN | VN | VN |
| 31 | 2 | Las niñas pequeños leen un libro | RECHAZA | NO | concordancia sustantivo-adjetivo | VN | VN | VN | VN | VN |
| 32 | 2 | El gato de la profesora duermen | RECHAZA | NO | concordancia sujeto-verbo con frase preposicional | VN | FP | VN | VN | VN |
| 33 | 3 | Las niñas que el profesor regañó están cansadas | ACEPTA | SI | concordancia a distancia con relativa de objeto | VP | VP | VP | VP | VP |
| 34 | 3 | Ana vio el perro con el telescopio | ACEPTA | SI | ambigüedad de adjunción | VP | VP | VP | VP | VP |
| 35 | 3 | Ana vio el perro en el parque con el telescopio | ACEPTA | SI | ambigüedad con dos frases preposicionales | VP | VP | VP | VP | VP |
| 36 | 3 | Luis dice que Ana dice que los niños comen | ACEPTA | SI | subordinadas anidadas | VP | VP* | VP | VP | VP |
| 37 | 3 | Llegaron los niños | ACEPTA | NO | orden verbo-sujeto | FN | VP | FN | FN | FN |
| 38 | 3 | Lee un libro | ACEPTA | NO | sujeto tácito | FN | FN | FN | FN | FN |
| 39 | 3 | Ayer los niños comieron mucho | ACEPTA | NO | adverbio antepuesto | FN | VP | FN | VP | VP |
| 40 | 3 | Ana , Luis y Pedro son alta , alto y alto respectivamente | ACEPTA | NO | dependencias cruzadas | FN | VP | FN | FN | FN |
| 41 | 3 | El perro que el niño vio ladra | ACEPTA | SI | relativa de objeto | VP | FN | VP | VP | VP |
| 42 | 3 | Los niños que leen libros están felices | ACEPTA | NO | plural sin determinante dentro de la relativa | FN | VP | FN | VP | VP |
| 43 | 3 | Las niñas que el profesor regañó están cansados | RECHAZA | NO | concordancia a distancia | VN | VN | VN | VN | VN |
| 44 | 3 | Las niñas que el profesor regañó el libro están cansadas | RECHAZA | NO | hueco de la relativa ocupado | VN | FP | VN | VN | VN |
| 45 | 3 | Ana , Luis y Pedro son alto , alto y alta respectivamente | RECHAZA | NO | dependencias cruzadas en orden espejo | VN | FP | VN | VN | VN |
| 46 | 3 | Ana y Luis son alto y alta respectivamente | RECHAZA | NO | dependencias cruzadas mal emparejadas | VN | FP | VN | VN | VN |
| 47 | 3 | Los niños que el profesor regañó está cansados | RECHAZA | NO | concordancia a distancia sujeto-cópula | VN | VN | VN | VN | VN |
| 48 | 3 | El perro que el niño vio el gato ladra | RECHAZA | NO | hueco de la relativa ocupado | VN | VN | VN | VN | VN |
