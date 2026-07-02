| 1. Arquitectura |     | del       | Procesador |     | STX4 |
| --------------- | --- | --------- | ---------- | --- | ---- |
| 1.1. Modelo     | de  | Registros |            |     |      |
La CPU del sistema RTM32, llamada STX4, es un procesador RISC de 32 bits ortogonal
que cuenta con un banco de 32 registros de prop(cid:243)sito general para el usuario numerados de 0
a 31 como se observa en la tabla 1.1 donde se exhibe la designaci(cid:243)n usada por el ensamblador
(mnemonic) para cada uno y el prop(cid:243)sito o convenci(cid:243)n que deberÆ seguir el programador y/o
| la herramienta | de desarrollo | que haga                             | uso de | los mismos. |     |
| -------------- | ------------- | ------------------------------------ | ------ | ----------- | --- |
| Reg.           | Mnemonic      | Prop(cid:243)sito|Convenci(cid:243)n |        |             |     |
| $0             | $zero         | Hardwired                            | a      | cero 1      |     |
$1 $at Registro temporario de uso habitual para el ensamblador
| $2,$3 | $k0,$k1 | Reservados | para | el sistema |     |
| ----- | ------- | ---------- | ---- | ---------- | --- |
$4,...,$7 $a0,...,$a3 Registros para paso de argumentos de funci(cid:243)n
$8,$9 $v0,$v1 Registros de retorno de valor de una funci(cid:243)n
$10,...,$19 $t0,...,$t9 Registros temporarios de prop(cid:243)sito general
| $20,...,$27 | $s0,...,$s7 |                   |                      |                      |         |
| ----------- | ----------- | ----------------- | -------------------- | -------------------- | ------- |
|             |             | Registros         | almacenables         | de prop(cid:243)sito | general |
| $28         | $fp         | Registro          | puntero              | de marco             |         |
| $29         | $gp         | Registro          | puntero              | global               |         |
| $30         | $sp         | Registro          | puntero              | de pila              |         |
| $31         | $ra         | Direcci(cid:243)n | de                   | retorno              |         |
|             | Tabla       | 1.1:              |                      |                      |         |
|             |             | Uso               | y convenci(cid:243)n | de los registros     | RTM32   |
El registro cero ($zero o $0) siempre contiene el valor 0. EstÆ cableado en el hardware,
as(cid:237) que no se puede modi(cid:28)car, aunque puede usarse como destino en cualquier instrucci(cid:243)n.
El registro $at (Assembler Temporary) se usa para valores temporales dentro de pseudo-
instrucciones. No se preserva entre function calls. Por ejemplo, con el comando (slt $at,
$a0, $s2), $at se setea en 1 si $a0 es menor que $s2; de lo contrario, se setea en 0.
Los registros $v0,$v1 se usan para retornar valores desde funciones. No se preservan entre
subrutinas (function calls). Normalmente solo se usa $v0 pero es posible retornar valores de
64 bits mediante $v1 (MSB). Dado que esto œltimo no es usual este registro puede usarse
| tambiØn como | un temporal | con el alias | $t10. |     |     |
| ------------ | ----------- | ------------ | ----- | --- | --- |
Los registros $a0,...,$a3 (argument) se usan para pasar argumentos a funciones. No se pre-
servan entre function calls al igual que los registros temporales $t0,...,$t9 (temporaries) que
son usados por el assembler o por el programador de assembly para almacenar valores in-
termedios. Los registros $s0,...,$s7 (Saved Temporary) se usan para almacenar valores de
mayor duraci(cid:243)n y s(cid:237) se preservan entre function calls. Los registros $k0,$k1 estÆn reservados
para uso del kernel del sistema operativo. Pueden cambiar de forma impredecible en cualquier
| momento porque | son utilizados | por | los interrupt | handlers. |     |
| -------------- | -------------- | --- | ------------- | --------- | --- |
Los registros de puntero (pointer registers) son una familia de registros que contiene direc-
ciones de memoria, a lo que se les asigna funciones muy particulares. Todos ellos se preservan
entre function calls y no todos son de uso obligatorio, por lo que pueden cumplir una funci(cid:243)n
secundaria con otro alias. Por ejempo $fp suele ser $s8 y $gp es $t10. Es importante enteder
que mientras se los use como otros registros no podrÆ ser punteros y viceversa.
1

Cap(cid:237)tulo 1. Arquitectura del Procesador STX4 Manual de Usuario RTM32
|     | A continuaci(cid:243)n |     |     | detallamos | la  | funci(cid:243)n | asignada | a cada uno | de ellos: |     |
| --- | ---------------------- | --- | --- | ---------- | --- | --------------- | -------- | ---------- | --------- | --- |
Puntero global $gp (Global Pointer): normalmente guarda un puntero al Ærea de datos
globales (para que pueda accederse usando memory o(cid:27)set addressing).
Punterodepila$sp(Stack Pointer):seusaparaalmacenarladirecci(cid:243)nadondeapunta
|     | la  | pila actualmente. |     |     |     |     |     |     |     |     |
| --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Puntero de marco $fp (Frame Pointer): se usa para almacenar la direcci(cid:243)n base del
|     | marco | de  | pila | (Stack | Frame). |     |     |     |     |     |
| --- | ----- | --- | ---- | ------ | ------- | --- | --- | --- | --- | --- |
Direcci(cid:243)n de retorno $ra (Return Address): almacena la direcci(cid:243)n de retorno (la ubica-
ci(cid:243)n del programa a la que una funci(cid:243)n debe volver). Este puntero es fundamental para
las instrucciones JAL y JALR, ya que su comportamiento respecto de este registro estÆ
|     | cableado |     | en el | procesador. |     |     |     |     |     |     |
| --- | -------- | --- | ----- | ----------- | --- | --- | --- | --- | --- | --- |
Todos los registros mencionados son utilizados regularmente en la CPU y accesible a
travesdelasinstruccionesperohayotrosregistroscomoelcontadordeprograma$pc(program
counter)queesmanipuladoexclusivamenteporlaCPUeindirectamenteporlasinstrucciones
de cambio de (cid:29)ujo. Los registros de funciones especiales (special function registers) permiten
inspeccionaroseteardistintascondicionesdellaCPUyseaccedenenformaindirectamediante
instrucciones espec(cid:237)(cid:28)cas como CFT y CTS. La CPU STX4 tiene 5 registros especiales que
| detallamos |     | a continuaci(cid:243)n: |     |     |     |     |     |     |     |     |
| ---------- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Palabra de estado del programa $psw (Program Status Word): almacena el estado de
ejecuci(cid:243)n del procesador, incluyendo las banderas aritmØticas, el nivel de privilegio y el
|     | estado | global |     | de las interrupciones. |     |     |     |     |     |     |
| --- | ------ | ------ | --- | ---------------------- | --- | --- | --- | --- | --- | --- |
Registro de causa de la excepci(cid:243)n $ecr (Exception Cause Register): contiene el c(cid:243)digo
que identi(cid:28)ca la excepci(cid:243)n o interrupci(cid:243)n que provoc(cid:243) la transferencia de control al
|     | manejador |     | correspondiente. |     |     |     |     |     |     |     |
| --- | --------- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- |
Contador de programa de la excepci(cid:243)n $epc (Exception Program Counter): almacena la
direcci(cid:243)n de la instrucci(cid:243)n cuya ejecuci(cid:243)n fue interrumpida por la excepci(cid:243)n o interrup-
|     | ci(cid:243)n, | permitiendo |     | reanudar |     | la ejecuci(cid:243)n | cuando | corresponda. |     |     |
| --- | ------------- | ----------- | --- | -------- | --- | -------------------- | ------ | ------------ | --- | --- |
Direcci(cid:243)n virtual incorrecta $bva (Bad Virtual Address): almacena la direcci(cid:243)n virtual
|     | que | origin(cid:243) | una | excepci(cid:243)n |     | de acceso | a memoria. |     |     |     |
| --- | --- | --------------- | --- | ----------------- | --- | --------- | ---------- | --- | --- | --- |
Registro base vectorizado $vbr (Vector Base Register): contiene la direcci(cid:243)n base de la
|      | tabla | de       | vectores | de excepci(cid:243)n |                     | e   | interrupci(cid:243)n. |     |     |     |
| ---- | ----- | -------- | -------- | -------------------- | ------------------- | --- | --------------------- | --- | --- | --- |
| 1.2. |       | Formatos |          | de                   | Instrucci(cid:243)n |     |                       |     |     |     |
Las instrucciones constan de un ancho (cid:28)jo de 32 bits y se decodi(cid:28)can mediante campos bit
a bit estructurados en cuatro tipos llamados: R, I, L y J. Todas las instrucciones comparten
el mismo campo llamado opcode o c(cid:243)digo de operaci(cid:243)n (operation code) formado por los
primeros 5 bits mÆs signi(cid:28)cativos (bit 27 al 31). El valor del opcode identi(cid:28)ca al tipo de
instrucci(cid:243)n como se muestra en la tabla A.1. No todos los opcodes son vÆlidos, por ejemplo
0x22 no lo es y por lo tanto cualquier instrucci(cid:243)n que utilice dichos opcodes son instrucciones
| invÆlidas |     | y el | uso de | los mismas |     | genera | excepciones. |     |     |     |
| --------- | --- | ---- | ------ | ---------- | --- | ------ | ------------ | --- | --- | --- |
El formato tipo R (register) que se muestra en la (cid:28)gura 1.1 se utiliza principalmente para
operaciones aritmØticas y l(cid:243)gicas entre registros, as(cid:237) como otra variedad de operaciones como
desplazamientos, movimientos en la memoria y tareas mÆs espec(cid:237)(cid:28)cas.
| 1.2. | Formatos |     | de Instrucci(cid:243)n |     |     |     |     |     |     | 2   |
| ---- | -------- | --- | ---------------------- | --- | --- | --- | --- | --- | --- | --- |

Cap(cid:237)tulo 1. Arquitectura del Procesador STX4 Manual de Usuario RTM32
|     | 31     | 27  | 26  | 22 21  | 17 16        | 12 11  | 7 6 5 |      | 0   |     |
| --- | ------ | --- | --- | ------ | ------------ | ------ | ----- | ---- | --- | --- |
|     | opcode |     | rs  | rt     | rd           | aux    | X     | func |     |     |
|     |        |     |     | Figura | 1.1: Formato | tipo R |       |      |     |     |
C(cid:243)mo todas comparten el mismo opcode, la CPU las diferencia por el campo func o funci(cid:243)n
(function) que se encuentra en los 6 bits menos signi(cid:28)cativos (bit 0 al 5). En la tabla A.2 se
provee una lista de las instrucciones tipo R y sus valores de funci(cid:243)n asociados.
Los campos rs, rt y rd especi(cid:28)can registros (de all(cid:237) el nombre de tipo R), haciendo referencia
al registro fuente (source register), el registro temporal o secundario (temporal register)
y el registro destino (destiny register), pero el campo que estÆ entre los bits 8 y 12 es
mÆs complejo de explicar ya que cumple dos funciones y por eso se le llama aux. En algunas
operaciones constituye una referencia auxiliar pero en otras es una constante inmediata
de 5 bits que puede tomar valores entre 0 y 31. Los detalles sobre su uso en las operaciones
| que | sean afectadas |     | se discutirÆ | mÆs adelante | segœn la | operaci(cid:243)n. |     |     |     |     |
| --- | -------------- | --- | ------------ | ------------ | -------- | ------------------ | --- | --- | --- | --- |
El formato tipo I o inmediato (immediate) se utiliza para las operaciones que requieren
del uso de una constante imm para resolver la instrucci(cid:243)n. El nombre proviene del modo de
direccionamiento llamado igual, ya que el operando estÆ inmediatamente anexo a la propia
instrucci(cid:243)n. Su estructura se muestra en la (cid:28)gura 1.2 y se compone de 4 campos. En este
formato el campo opcode determina exactamente cuÆl es la instrucci(cid:243)n.
|     | 31     | 27  | 26  | 22 21 | 17 16 |     |     |     | 0   |     |
| --- | ------ | --- | --- | ----- | ----- | --- | --- | --- | --- | --- |
|     | opcode |     | rs  | rt    |       |     |     |     |     |     |
imm
|     |     |     |     | Figura | 1.2: Formato | tipo I |     |     |     |     |
| --- | --- | --- | --- | ------ | ------------ | ------ | --- | --- | --- | --- |
Este tipo de instrucci(cid:243)n se utiliza para movimientos de carga o descarga en la memoria donde
es necesario calcular una direcci(cid:243)n efectiva EA (e(cid:27)ective address) dependiendo de un o(cid:27)set
(imm). El campo rs siempre especi(cid:28)ca el registro que se va a cargar o descargar, mientras que
rt es un apuntador (pointer) y el campo imm almacena una constante inmediata de 17 bits en
complementoadosllamadadesplazamiento(o(cid:27)set).Lasumadelpunteroysudesplazamiento
conforman la direcci(cid:243)n efectiva EA y a este modo de direccionamiento se lo conoce como
modo indexado. Esta es la direcci(cid:243)n de memoria donde se encuentra el dato a traer a la CPU
| o donde | la  | CPU lo | va a descarga. |     |     |     |     |     |     |     |
| ------- | --- | ------ | -------------- | --- | --- | --- | --- | --- | --- | --- |
ADVERTENCIA
Algunas lecturas y escrituras de memoria realizan veri(cid:28)caci(cid:243)n de alineaci(cid:243)n (alignment
checking).Unadirecci(cid:243)nEAnoalineadautilizadaporunainstrucci(cid:243)nquenecesitaope-
rarconpalabras,comoporejemploLWgenerarÆunaexcepci(cid:243)ndeteniendoelprocesador
|     | si EA no | es mœltiplo | de  | 4.  |     |     |     |     |     |     |
| --- | -------- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
Este formato tambien se utiliza para operaciones de salto condicional (branch). Segœn
el tipo de operaci(cid:243)n BEQ, BNE, etc, luego de analizar la condici(cid:243)n, si la misma es verdadera
entonces la CPU realizarÆ el salto correspondiente cambiando el valor del PC a uno nuevo
cuyo cÆlculo se explica a continuaci(cid:243)n. La clave para entender imm es que no almacena una
≈ ±216
direcci(cid:243)n de salto sino un o(cid:27)set en palabras que permite tener un desplazamiento de
hacia adelante o atras debido a que estÆ almacenado en complemento a dos. La direcci(cid:243)n se
| salto | responde | a la | f(cid:243)rmula:    |     |     |     |     |     |     |     |
| ----- | -------- | ---- | ------------------- | --- | --- | --- | --- | --- | --- | --- |
| 1.2.  | Formatos | de   | Instrucci(cid:243)n |     |     |     |     |     |     | 3   |

Cap(cid:237)tulo 1. Arquitectura del Procesador STX4 Manual de Usuario RTM32
|     |     |     |     |     |     | PC =PC+4∗imm |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------------ | --- | --- | --- | --- | --- |
La constante 4 que se traduce en el sentido que no es necesario guardar los dos œltimos bits
de la direcci(cid:243)n es porque este procesador al ser regular no admite que ninguna instrucci(cid:243)n no
| estØ | alineada | (direcciones |     | mœltiplos |     | de 4). |     |     |     |     |     |
| ---- | -------- | ------------ | --- | --------- | --- | ------ | --- | --- | --- | --- | --- |
Por œltimo, tenemos las instrucciones SLTI y SLTIU han quedado como un rezago hist(cid:243)-
rico que permite testear la condici(cid:243)n menor que con y sin signo respecto de una constante.
Permiten algunas comparaciones elementales sin necesidad de tener que tener todos los datos
previamente en registros, lo cuÆl puede ser muy conveniente, as(cid:237) como el caso de ADDI que es
| extremadamente |     |     | util para | incrementar |     | o   | decrementar | contadores. |     |     |     |
| -------------- | --- | --- | --------- | ----------- | --- | --- | ----------- | ----------- | --- | --- | --- |
ElformatoLesunavariantedelformatoI.Existeporqueesabsurdoutilizarunaconstante
|     |     |     |     |     |     |     | ANDI, | ORI | XORI. |     |     |
| --- | --- | --- | --- | --- | --- | --- | ----- | --- | ----- | --- | --- |
de 17 bits para operaciones l(cid:243)gicas como y Por lo tanto bÆsicamente se
comprimi(cid:243) imm a 16 bits quedando un bit h disponible para indicar si dicha constante opera
2
en la parte inferior de la palabra (h = 0) o superior (h = 1) de la palabra .
Solo queda mencionar LUI que carga la constante imm en los 16 bits MSB del registro espe-
ci(cid:28)cado por rt dejando los restantes en 0s. Esta instrucci(cid:243)n es vital para cargar constantes
| arbitrarias |        | de 32 | bits en | registros | mediante |      | la combinaci(cid:243)n |      | con ORI. |     |     |
| ----------- | ------ | ----- | ------- | --------- | -------- | ---- | ---------------------- | ---- | -------- | --- | --- |
|             | 31     |       | 27 26   |           | 22 21    |      | 17 16 15               |      |          | 0   |     |
|             | opcode |       |         | rs        |          | rt   | h                      |      | imm      |     |     |
|             |        |       |         |           | Figura   | 1.3: | Formato                | tipo | L        |     |     |
Finalmente arribamos al œltimo formato que se muestra en la (cid:28)gura 1.4. Las instrucciones
tipo J, se utilizan para los saltos incondicionales J y JAL con sus respectivos opcodes 0x2
y 0x3. BÆsicamente poseen dos campos, el opcode para identi(cid:28)carlas y la direcci(cid:243)n de salto
jump address en palabras de memoria no signadas (unsigned). Esto signi(cid:28)ca al igual que en
los branch que este valor debe almacenarse omitiendo los œltimos dos bits de la direcci(cid:243)n a
saltar.
|     | 31     |     | 27 26 |     |        |      |         |         |     | 0   |     |
| --- | ------ | --- | ----- | --- | ------ | ---- | ------- | ------- | --- | --- | --- |
|     | opcode |     |       |     |        |      | jump    | address |     |     |     |
|     |        |     |       |     | Figura | 1.4: | Formato | tipo    | J   |     |     |
La œnica particularidad relevante dado que el campo jump address es de 27 bits la direcci(cid:243)n
almacenada representa 29 bits, quedan 3 bits faltantes para obtener la direcci(cid:243)n (cid:28)nal de 32
|     |     |     |     |     |     |     | PC (PC[31:29]) |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------------- | --- | --- | --- | --- |
bits. Estos 3 bits se extraen del los 3 MSB del y se concatenan con los 27 bits
| de  | jump address |     | mÆs | dos bits | que | son siempre | 0s. |     |     |     |     |
| --- | ------------ | --- | --- | -------- | --- | ----------- | --- | --- | --- | --- | --- |
2Actualmente
|      |          | hay | un bug                 | importante |     | a solucionar | en la | instruccion | ANDI |     |     |
| ---- | -------- | --- | ---------------------- | ---------- | --- | ------------ | ----- | ----------- | ---- | --- | --- |
| 1.2. | Formatos |     | de Instrucci(cid:243)n |            |     |              |       |             |      |     | 4   |

| A. Instruction |      |       | Set      | Reference |           |     |     |     |     |     |
| -------------- | ---- | ----- | -------- | --------- | --------- | --- | --- | --- | --- | --- |
| Opcode         | Type | Mnemo | Operands |           | Operation |     |     |     |     |     |
| 00000          | R    |       |          |           | see table | A.2 |     |     |     |     |
(1)
| 00001 | I   | ADDI | rs  | rt imm | R[rt] | = R[rs] | + SE(imm) |     |     |     |
| ----- | --- | ---- | --- | ------ | ----- | ------- | --------- | --- | --- | --- |
(2)
| 00010 | J   | J   | address |     | PC =  | E(address) |      |      |            |     |
| ----- | --- | --- | ------- | --- | ----- | ---------- | ---- | ---- | ---------- | --- |
| 00011 | J   | JAL | address |     | R[31] | = PC       | + 4; | PC = | E(address) |     |
00100 L ANDI/H rs rt ims R[rt] = R[rs] & ZE(ims)/ZC(ims) (3,4)
| 00101 | L   | ORI/H | rs  | rt ims | R[rt] | = R[rs] | | ZE(ims)/ZC(ims) |     |     |     |
| ----- | --- | ----- | --- | ------ | ----- | ------- | ----------------- | --- | --- | --- |
⊕
| 00110 | L   | XORI/H | rs  | rt ims | R[rt]    | = R[rs]            | ZE(ims)/ZC(ims) |              |             |     |
| ----- | --- | ------ | --- | ------ | -------- | ------------------ | --------------- | ------------ | ----------- | --- |
| 00111 | L   | LUI    | rt  | ims    | R[rt]    | = ZC(ims)          |                 |              |             |     |
| 01000 | I   | LW     | rs  | rt imm | R[rt]    | = M[EA(rs,         |                 | imm)]        | (5)         |     |
| 01001 | I   | SW     | rs  | rt imm | M[EA(rs, |                    | imm)]           | = R[rt]      |             |     |
| 01010 | I   | SH     | rs  | rt imm | M[EA(rs, |                    | imm)][15:0]     | =            | R[rt][15:0] |     |
| 01011 | I   | SB     | rs  | rt imm | M[EA(rs, |                    | imm)][7:0]      | =            | R[rt][7:0]  |     |
| 01100 | I   | LH     | rs  | rt imm | R[rt]=   | SHE(M[EA(rs,       |                 | imm)][15:0]) |             | (6) |
| 01101 | I   | LHU    | rs  | rt imm | R[rt]=   | ZE(M[addr][15:0]}) |                 |              |             |     |
(7)
01110 I LB rs rt imm R[rt]={24{M[addr](7:0)[7]}, M[addr](7:0)}
(8)
| 01111 | I   | LBU | rs  | rt imm | R[rt]={24’b0, |     | M[addr](7:0)} |     |     |     |
| ----- | --- | --- | --- | ------ | ------------- | --- | ------------- | --- | --- | --- |
(9)
10000 I BEQ rs rt imm if (R[rs] == R[rt]) PC=PC+4+Branch(imm)
10001 I BNE rs rt imm if (R[rs] != R[rt]) PC=PC+4+Branch(imm)
| 10010 | I   | BLT | rs  | rt imm | if (R[rs] | <   | R[rt]) | PC=PC+4+Branch(imm) |     |     |
| ----- | --- | --- | --- | ------ | --------- | --- | ------ | ------------------- | --- | --- |
| 10011 | I   | BGT | rs  | rt imm | if (R[rs] | >   | R[rt]) | PC=PC+4+Branch(imm) |     |     |
10100 I BLE rs rt imm if (R[rs] <= R[rt]) PC=PC+4+Branch(imm)
10101 I BGE rs rt imm if (R[rs] >= R[rt]) PC=PC+4+Branch(imm)
| 10110          | I               | SLTI          | rs        | rt imm   | R[rt]       | = (R[rs]          | <        | SE(imm))  | ? 1 : | 0   |
| -------------- | --------------- | ------------- | --------- | -------- | ----------- | ----------------- | -------- | --------- | ----- | --- |
| 10111          | I               | SLTIU         | rs        | rt imm   | R[rt]       | = (R[rs]          | <        | ZE(imm))  | ? 1   | : 0 |
|                |                 | Tabla         | A.1:      | RTM32    | Instruction | Set               | sorted   | by opcode |       |     |
| (1) SE(imm)    | = {15’imm[16]), |               | imm}      | extiende | imm         | con               | signo    |           |       |     |
| (2) E(address) | =               | {PC+4[31:29], | address,  |          | 2’b0}       | extiende          | address  |           |       |     |
| (3) ZE(ims)    | = {16’b0,       | imm}          | extiende  | ims      | con 0s      |                   |          |           |       |     |
| (4) ZC(ims)    | = {imm,         | 16’b0}        | concatena |          | ims con     | 0s                |          |           |       |     |
| (5) EA(rs,     | imm) =          | R[rs]         | + SE(imm) | calcula  | la          | direcci(cid:243)n | efectiva | EA        |       |     |
(6) SHE(h) = {16’{h[15]}, h} extiende h (media palabra) usando signo
| (7) SBE(byte) | =   | {24’{byte[7]}, | byte}          | extiende | byte        | usando |     | signo |     |     |
| ------------- | --- | -------------- | -------------- | -------- | ----------- | ------ | --- | ----- | --- | --- |
| (8) ZBE(byte) | =   | {24’b0,        | byte} extiende |          | byte usando |        | 0s  |       |     |     |
(9) Branch(imm) = {13’{imm[16]}, imm, 2’b0} calcula el o(cid:27)set de salto
5

ApØndice A. Instruction Set Reference Manual de Usuario RTM32
| Func Mnemo | Operands | Operation |     |     |
| ---------- | -------- | --------- | --- | --- |
≪
| 000000 SLL  | rs rt rd aux | R[rd] = | R[rt] aux          |     |
| ----------- | ------------ | ------- | ------------------ | --- |
| 000001 SRL  | rs rt rd aux | R[rd] = | R[rt] ≫ aux        |     |
| 000010 SRA  | rs rt rd aux | R[rd]=  | R[rs] ⋙ aux        |     |
| 000011 SLLR | rs rt rd     | R[rd] = | R[rt] ≪ R[rs][4:0] |     |
≫
| 000100 SRLR | rs rt rd | R[rd] = | R[rt] R[rs][4:0]   |     |
| ----------- | -------- | ------- | ------------------ | --- |
| 000101 SRAR | rs rt rd | R[rd] = | R[rt] ⋙ R[rs][4:0] |     |
| 000110 CFS  | rs aux   | R[rs] = | S[aux]             |     |
| 000111 CTS  | rs aux   | S[aux]  | = R[rs]            |     |
| 001000 AND  | rs rt rd | R[rd] = | R[rs] & R[rt]      |     |
| 001001 OR   | rs rt rd | R[rd] = | R[rs] | R[rt]      |     |
| 001010 XOR  | rs rt rd | R[rd] = | R[rs] ⊕ R[rt]      |     |
¬
| 001011 NOR  | rs rt rd | R[rd] = | (R[rs] | R[rt]) |             |
| ----------- | -------- | ------- | --------------- | ----------- |
| 001100 SLT  | rs rt rd | R[rd] = | (R[rs] < R[rt]) | ? 1 : 0     |
| 001101 SLTU | rs rt rd | R[rd] = | (R[rs] < R[rt]) | ? 1 : 0 (8) |
| 001110 JR   | rs       | PC =    | R[rs]           |             |
| 001111 JALR | rs rt    | R[31] = | PC + 4; PC      | = R[rs]     |
010000 LHX rs rt rd R[rt]={16{M[R[rs]+R[rd]](15:0)[15], M[R[rs]+R[rd]](15:0)}
| 010001 LHUX | rs rt rd | R[rt]={16’b0, | M[R[rs]+R[rd]](15:0)} |     |
| ----------- | -------- | ------------- | --------------------- | --- |
010010 LBX rs rt rd {24{M[R[rs]+R[rd]](7:0)[7], M[R[rs]+R[rd]](7:0)}
| 010011 LBUX | rs rt rd | R[rt]={24’b0, | M[R[rs]+R[rd]](7:0)}          |     |
| ----------- | -------- | ------------- | ----------------------------- | --- |
| 010100 LWX  | rs rt rd | R[rt]=        | M[R[rs]+R[rd]]                |     |
| 010101 MUL  | rs rt rd | R[rd] =       | {R[rs] (cid:214) R[rt]}(31:0) |     |
(cid:214)
| 010110 MULH  | rs rt rd | R[rd] = | {R[rs] R[rt]}(63:32) |     |
| ------------ | -------- | ------- | -------------------- | --- |
|              |          |         | (cid:214)            | (8) |
| 010111 MULHU | rs rt rd | R[rd] = | {R[rs] R[rt]}(63:32) |     |
| 011000 DIV   | rs rt rd | R[rd] = | R[rs] / R[rt]        |     |
| 011001 DIVU  | rs rt rd | R[rd] = | R[rs] / R[rt]        | (8) |
| 011010 REST  | rs rt rd | R[rd] = | R[rs]% R[rt]         |     |
(8)
| 011011 RESTU | rs rt rd   | R[rd] = | R[rs]% R[rt]        |              |
| ------------ | ---------- | ------- | ------------------- | ------------ |
| 011100 ADD   | rs rt rd   | R[rd] = | R[rs] + R[rt]       |              |
| 011101 SUB   | rs rt rd   | R[rd] = | R[rs] − R[rt]       |              |
| 100000 TRAP  | aux        | EPC =   | PC + 4; PC          | = M[aux ≪ 2] |
| 100001 RFT   |            | PC =    | EPC                 |              |
|              | Tabla A.2: | R-type  | instructions sorted | by func      |
6
