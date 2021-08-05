from matplotlib import colors
import numpy as np
import pandas as pd 
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import re
import geopandas as gpd

#Creamos el DataFrame

#Leemos el Excel por parte de la libreria Openpyxl
archive = pd.ExcelFile('RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx')

#Creamos el DataFrame por medio de la lectura del Excel
df2 = pd.read_excel(archive,"SEGUIMIENTO DE CASOS COVID 19",usecols="A:T",skiprows=range(0,13))

#Organizamos los datos por medio de la funcion Iloc para manejar columnas y filas en nuestro DF
DFCasos = pd.DataFrame({'Sexo':df2.iloc[:,2],
                        'Edad':df2.iloc[:,3],
                        'Residencia':df2.iloc[:,4],
                        'Derechohabiencia':df2.iloc[:,7],
                        'Fecha Notif':df2.iloc[:,8],
                        'Toma de muestra':df2.iloc[:,10],
                        'Resultado':df2.iloc[:,12],
                        'Fecha Result':df2.iloc[:,13],
                        'Estatus':df2.iloc[:,14],
                        'Pais Procedente':df2.iloc[:,15]})

#Remplazar datos erroneos en el DataFrame

#Rellenamos Vacios
DFCasos['Fecha Result'] = DFCasos['Fecha Result'].fillna('01/01/2000  12:00:00 a. m.')

#Remplazamos Datos por medio de funciones regulares REGEX
#    Estas funciones nos indican que debemos tomar ciertos valores que contengan una serie de caracteres para poder hacer un remplazo de datos
DFCasos['Pais Procedente'] = DFCasos['Pais Procedente'].fillna('MÉXICO')
DFCasos['Pais Procedente'] = DFCasos['Pais Procedente'].replace(regex=[r'^MEX.*', r'^MÉX.*'], value='MÉXICO')

DFCasos['Estatus'] = DFCasos['Estatus'].replace(regex=[r'^AM.*',r'^AB.*',r'^MBU.*',r'^ AMB.*'], value='AMBULATORIO')
DFCasos['Estatus'] = DFCasos['Estatus'].replace(regex=[r'^AL.*'], value='ALTA')
DFCasos['Estatus'] = DFCasos['Estatus'].replace(regex=[r'^DE.*',r'^CA.*'], value='DEFUNCION')
DFCasos['Estatus'] = DFCasos['Estatus'].replace(regex=[r'^HOS.*',r'^TER.*',r'^PED.*'], value='HOSPITALIZADO')

DFCasos['Residencia'] = DFCasos['Residencia'].fillna('FORANEO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'^NIC.*',r'^CHIA.*',r'(^.*JA.*$)',r'(^.*VER.*$)',r'^HID.*',r'^DA.*',r'(^.*EEUU.*$)',r'^MOR.*',r'^PUEB.*',r'^SONO.*',r'(^.*JUAR.*$)'], value='FORANEO')   
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*GUSTAVO.*$)',r'(^.*GAM.*$)'], value='GUSTAVO A. MADERO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*IZTAP.*$)',r'(^.*APA.*$)'], value='IZTAPALAPA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*IZTAC.*$)',r'(^.*LCO.*$)',r'(^.*AGRICOLA.*$)',r'(^.*ORIENTAL.*$)'], value='IZTACALCO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*CHIMA.*$)',r'(^.*HUACAN.*$)'], value='CHIMALHUACAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*NEZA.*$)',r'(^.*AV..*$)',r'(^.*CORO.*$)'], value='NEZAHUALCOYOTL')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*BENI.*$)'], value='BENITO JUAREZ')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*CUAU.*$)',r'(^.*CUAH.*$)'], value='CUAUHTEMOC')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*COYO.*$)'], value='COYOACAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*CUAJ.*$)'], value='CUAJIMALPA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*ECAT.*$)'], value='ECATEPEC')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*XOCH.*$)'], value='XOCHIMILCO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*ALVARO.*$)'], value='ALVARO OBREGON')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*AMECA.*$)',r'(^.*CAMINO.*$)'], value='AMECAMECA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*JUCHITE.*$)'], value='JUCHITEPEC')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TLA.*$)'], value='TLALPAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*AZCAP.*$)'], value='AZCAPOTZALCO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*IXTA.*$)',r'(^.*LA MAG.*$)'], value='IXTAPALUCA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*MIGUE.*$)'], value='MIGUEL HIDALGO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*VENU.*$)'], value='VENUSTIANO CARRANZA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*PAZ.*$)',r'(^.*REYES.*$)'], value='LOS REYES - LA PAZ')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TECA.*$)',r'(^.*AMAC.*$)'], value='TECAMAC')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TEX.*$)',r'(^.*COCO.*$)'], value='TEXCOCO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*CHIN.*$)',r'(^.*CONCUAC.*$)'], value='CHINCONCUAC')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TULTE.*$)',r'(^.*SAN PABLO.*$)'], value='TULTEPEC')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*NAUC.*$)'], value='NAUCALPAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*ATEN.*$)'], value='ATENCO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*HUIX.*$)'], value='HUIXQUILUCAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*ACOL.*$)'], value='ACOLMAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TOL.*$)'], value='TOLUCA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*LER.*$)'], value='LERMA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TEPET.*$)',r'(^.*LIXPA.*$)'], value='TEPETLIXPA')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TEOL.*$)'], value='TEOLOYUCAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*CHICO.*$)'], value='CHICOLOAPAN')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*NICOL.*$)'], value='NICOLAS ROMERO')
DFCasos['Residencia'] = DFCasos['Residencia'].replace(regex=[r'(^.*TENAN.*$)'], value='TENANGO DEL VALLE')

#Regex para encontrar una serie de letras en un string >> r'(^.*VER.*$)'

DFCasos['Derechohabiencia'] = DFCasos['Derechohabiencia'].fillna('NINGUNO')

DFCasos['Fecha Notif'] = DFCasos['Fecha Notif'].fillna('01/01/2000  12:00:00 a. m.')

DFCasos['Toma de muestra']=DFCasos['Toma de muestra'].fillna('PENDIENTE')
DFCasos['Toma de muestra'] = DFCasos['Toma de muestra'].replace(regex=[r'(^.*PENS.*$)',r'(^.*PEND.*$)',r'(^.*NEG.*$)',r'(^.*POS.*$)'], value='PENDIENTE')
DFCasos['Toma de muestra'] = DFCasos['Toma de muestra'].replace(regex=[r'(^.*NO.*$)'], value='NO SE TOMÓ')

DFCasos['Resultado'] = DFCasos['Resultado'].fillna('SOSPECHOSO')
DFCasos['Resultado'] = DFCasos['Resultado'].replace(regex=[r'^POS.*', r'^´POS.*'], value='POSITIVO')
DFCasos['Resultado'] = DFCasos['Resultado'].replace(regex=[r'^NEG.*',r'^ NEG.*'], value='NEGATIVO')
DFCasos['Resultado'] = DFCasos['Resultado'].replace(regex=[r'^IN.*', r'^´NO.*',r'M.*',r'NO.*',r'PEN.*',r'REC.*',r'SIN.*'], value='SOSPECHOSO')

DFCasos['Fecha Result'] = DFCasos['Fecha Result'].fillna('PENDIENTE')
DFCasos['Fecha Result'] = DFCasos['Fecha Result'].replace(regex=[r'(^.*PENS.*$)',r'(^.*PEND.*$)'], value='PENDIENTE')
DFCasos['Fecha Result'] = DFCasos['Fecha Result'].replace(regex=[r'(^.*NO.*$)',r'(^.*ERR.*$)',r'(^.*DEF.*$)',r'(^.*SIN.*$)'], value='NO SE TOMÓ')
DFCasos['Fecha Result'] = DFCasos['Fecha Result'].replace(regex=[r'(^.*NEG.*$)'], value='NEGATIVO')
DFCasos['Fecha Result'] = DFCasos['Fecha Result'].replace(regex=[r'(^.*PO.*$)'], value='POSITIVO')


#Organizar los datos por Columna
dateinResult = DFCasos['Resultado'].str.findall(r'(^.*[A-Z].$)')
DFCasos['Fecha Result'], DFCasos['Resultado'] = np.where(dateinResult.isnull() ,[DFCasos['Resultado'],DFCasos['Fecha Result']],[DFCasos['Fecha Result'],DFCasos['Resultado']])

#Segunda normalizacion de datos
DFCasos['Fecha Result'] = DFCasos['Fecha Result'].replace(regex=[r'(^.*P.*$)',r'(^.*NE.*$)'], value='PENDIENTE')

DFCasos['Resultado'] = np.where(DFCasos['Resultado'].isin(['POSITIVO','NEGATIVO','SOSPECHOSO']),DFCasos['Resultado'],'SOSPECHOSO')
#Si necesitamos cambiar casos en los que no se parezca a ciertos datos aplicamos
#  'np.where(DFCasos['Resultado'].isin(['POSITIVO','NEGATIVO','SOSPECHOSO']),DFCasos['Resultado'],'SOSPECHOSO')'
DFCasos['Edad'] = DFCasos['Edad'].fillna('-1')
DFCasos['Edad'] = DFCasos['Edad'].replace(regex=[r'(^.*RN.*$)',r'(^.*D.*$)',r'(^.*ME.*$)',r'(^.*d.*$)',r'(^.*m.*$)'], value='0')

DFCasos['Sexo'] = DFCasos['Sexo'].fillna('SIN DATO')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*F.*$)'], value='F')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*M.*$)',r'(^.*H.*$)',r'(^.*N.*$)'], value='M')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*RN.*$)',r'(^.*D.*$)'], value= '0')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*AÑ.*$)'],value='')

ageinGender = DFCasos['Sexo'].str.findall(r'(^.*[A-Z].*$)')
DFCasos['Sexo'], DFCasos['Edad'] = np.where(ageinGender.isnull() ,[DFCasos['Edad'],DFCasos['Sexo']],[DFCasos['Sexo'],DFCasos['Edad']])

DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*F.*$)'], value='F')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*M.*$)',r'(^.*H.*$)',r'(^.*N.*$)',r'(^.*,M.*$)'], value='M')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*G.*$)',r'(^.*SN.*$)',r'(^.*X.*$)',r'(^.*R.*$)'], value='OTRO')

DFCasos['Edad'] = DFCasos['Edad'].replace(regex=[r'(^.*M.*$)',r'(^.*H.*$)',r'(^.*N.*$)',r'(^.*,M.*$)'], value='M')
DFCasos['Edad'] = np.where(~DFCasos['Edad'].isin(['M','F','H','NIÑO']),DFCasos['Edad'],'SIN DATO')
DFCasos['Sexo'] = np.where(DFCasos['Sexo'].isin(['M','F','OTRO']),DFCasos['Sexo'],'OTRO')
DFCasos['Edad'] = DFCasos['Edad'].replace(regex=[r'(^.*SIN DATO.*$)'], value='-1')
DFCasos['Edad'] = pd.to_numeric(DFCasos['Edad'])

#Exel de Verificacion de Datos
DFCasos.to_excel('Verificar.xlsx')

#Comenzamos a graficar los datos.

plt.close('all')

#Casos totales analizados por sexo
Sexos = DFCasos['Sexo'].value_counts()
Resultados = DFCasos['Resultado'].value_counts()
Colores = ['#b7094c','#a01a58','#892b64','#723c70','#5c4d7d','#455e89','#2e6f95','#1780a1','#0091ad','#33A7BD','#0077b6','#0096c7','#00b4d8','#48cae4']

DFCasos['Sexo'].value_counts().plot(kind='bar',figsize=(10, 10),rot=0,color=Colores)
plt.xlabel("Genero", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos de Posible COVID-19 por Genero",y=1.02)
fem = mpatches.Patch(color=Colores[0], label='Femenino')
masc = mpatches.Patch(color=Colores[1], label='Masculino')
otro = mpatches.Patch(color=Colores[2], label='Otro')
plt.legend(handles=[fem,masc,otro])
for index,data in enumerate(Sexos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Casos de Posible COVID-19 por Genero.png')


plt.figure()
DFCasos['Resultado'].value_counts().plot(kind='bar',figsize=(10, 10),rot=0,color=Colores)
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos COVID-19",y=1.02)
neg = mpatches.Patch(color=Colores[0], label='Negativo')
pos = mpatches.Patch(color=Colores[1], label='Positivo')
sos = mpatches.Patch(color=Colores[2], label='Sospechoso')
plt.legend(handles=[neg,pos,sos])
for index,data in enumerate(Resultados):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Casos COVID-19.png')

#Mascaras de datos
FemPos = DFCasos['Resultado'].str.contains('POSITIVO') & DFCasos['Sexo'].str.contains('F')
FemNeg = DFCasos['Resultado'].str.contains('NEGATIVO') & DFCasos['Sexo'].str.contains('F')
FemSos = DFCasos['Resultado'].str.contains('SOSPECHOSO') & DFCasos['Sexo'].str.contains('F')

MasPos = DFCasos['Resultado'].str.contains('POSITIVO') & DFCasos['Sexo'].str.contains('M')
MasNeg = DFCasos['Resultado'].str.contains('NEGATIVO') & DFCasos['Sexo'].str.contains('M')
MasSos = DFCasos['Resultado'].str.contains('SOSPECHOSO') & DFCasos['Sexo'].str.contains('M')

OtroPos = DFCasos['Resultado'].str.contains('POSITIVO') & DFCasos['Sexo'].str.contains('OTRO')
OtroNeg = DFCasos['Resultado'].str.contains('NEGATIVO') & DFCasos['Sexo'].str.contains('OTRO')
OtroSos = DFCasos['Resultado'].str.contains('SOSPECHOSO') & DFCasos['Sexo'].str.contains('OTRO')

Aux0 = FemPos.value_counts()
Aux1 = FemNeg.value_counts()
Aux2 = FemSos.value_counts()
NumeroCasos = [Aux0[1],Aux1[1],Aux2[1]]

plt.figure(figsize=(10, 10))
plt.bar('Positivos', Aux0[1], label = "Pos",color=Colores[0])
plt.bar('Negativos', Aux1[1], label = "Neg",color=Colores[1])
plt.bar('Sospechosos', Aux2[1], label = "Sos",color=Colores[2])
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos en genero Femenino",y=1.02)
pos = mpatches.Patch(color=Colores[0], label='Positivos')
neg = mpatches.Patch(color=Colores[1], label='Negativos')
sos = mpatches.Patch(color=Colores[2], label='Sospechosos')
plt.legend(handles=[pos,neg,sos])
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Casos en genero Femenino.png')


Aux0 = MasPos.value_counts()
Aux1 = MasNeg.value_counts()
Aux2 = MasSos.value_counts()
NumeroCasos = [Aux0[1],Aux1[1],Aux2[1]]

plt.figure(figsize=(10, 10))
plt.bar('Positivos', Aux0[1], label = "Pos",color=Colores[0])
plt.bar('Negativos', Aux1[1], label = "Neg",color=Colores[1])
plt.bar('Sospechosos', Aux2[1], label = "Sos",color=Colores[2])
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos en genero Masculino",y=1.02)
pos = mpatches.Patch(color=Colores[0], label='Positivos')
neg = mpatches.Patch(color=Colores[1], label='Negativos')
sos = mpatches.Patch(color=Colores[2], label='Sospechosos')
plt.legend(handles=[pos,neg,sos])
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Casos en genero Masculino.png')


Aux0 = OtroPos.value_counts()
Aux1 = OtroNeg.value_counts()
Aux2 = OtroSos.value_counts()
NumeroCasos = [Aux0[1],Aux1[1],Aux2[1]]

plt.figure(figsize=(10, 10))
plt.bar('Positivos', Aux0[1], label = "Pos",color=Colores[0])
plt.bar('Negativos', Aux1[1], label = "Neg",color=Colores[1])
plt.bar('Sospechosos', Aux2[1], label = "Sos",color=Colores[2])
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos en otros generos")
pos = mpatches.Patch(color=Colores[0], label='Positivos')
neg = mpatches.Patch(color=Colores[1], label='Negativos')
sos = mpatches.Patch(color=Colores[2], label='Sospechosos')
plt.legend(handles=[pos,neg,sos])
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+0.125, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Casos en otros generos.png')

plt.figure()
EstatusGenerales = DFCasos['Estatus'].value_counts()
DFCasos['Estatus'].value_counts().plot(kind='bar',figsize=(10, 10),rot=0,color=Colores)
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Estatus de casos de COVID-19",y=1.02)
Amb = mpatches.Patch(color=Colores[0], label='Ambulatorio')
Hosp = mpatches.Patch(color=Colores[1], label='Hospitalizado')
Def = mpatches.Patch(color=Colores[2], label='Defuncion')
Alta = mpatches.Patch(color=Colores[3], label='Alta')
plt.legend(handles=[Amb,Hosp,Def,Alta])
for index,data in enumerate(EstatusGenerales):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Estatus de casos de COVID-19.png')

FemAmb = DFCasos['Estatus'].str.contains('AMBULATORIO') & DFCasos['Sexo'].str.contains('F')
FemHos = DFCasos['Estatus'].str.contains('HOSPITALIZADO') & DFCasos['Sexo'].str.contains('F')
FemDef = DFCasos['Estatus'].str.contains('DEFUNCION') & DFCasos['Sexo'].str.contains('F')
FemAlta = DFCasos['Estatus'].str.contains('ALTA') & DFCasos['Sexo'].str.contains('F')

MasAmb = DFCasos['Estatus'].str.contains('AMBULATORIO') & DFCasos['Sexo'].str.contains('M')
MasHos = DFCasos['Estatus'].str.contains('HOSPITALIZADO') & DFCasos['Sexo'].str.contains('M')
MasDef = DFCasos['Estatus'].str.contains('DEFUNCION') & DFCasos['Sexo'].str.contains('M')
MasAlta = DFCasos['Estatus'].str.contains('ALTA') & DFCasos['Sexo'].str.contains('M')

OAmb = DFCasos['Estatus'].str.contains('AMBULATORIO') & DFCasos['Sexo'].str.contains('OTRO')
OHos = DFCasos['Estatus'].str.contains('HOSPITALIZADO') & DFCasos['Sexo'].str.contains('OTRO')
ODef = DFCasos['Estatus'].str.contains('DEFUNCION') & DFCasos['Sexo'].str.contains('OTRO')
OAlta = DFCasos['Estatus'].str.contains('ALTA') & DFCasos['Sexo'].str.contains('OTRO')

Aux0 = FemAmb.value_counts()
Aux1 = FemHos.value_counts()
Aux2 = FemDef.value_counts()
Aux3 = FemAlta.value_counts()
NumeroCasos = [Aux0[1],Aux1[1],Aux2[1],Aux3[1]]

plt.figure(figsize=(10, 10))
plt.bar('AMBULATORIO', Aux0[1], label = "Ambulatorio",color=Colores[0])
plt.bar('HOSPITALIZADO', Aux1[1], label = "Hospitalizado",color=Colores[1])
plt.bar('DEFUNCION', Aux2[1], label = "Defuncion",color=Colores[2])
plt.bar('ALTA', Aux3[1], label = "Alta",color=Colores[3])
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Estatus en casos femeninos",y=1.02)
Amb = mpatches.Patch(color=Colores[0], label='Ambulatorio')
Hosp = mpatches.Patch(color=Colores[1], label='Hospitalizado')
Def = mpatches.Patch(color=Colores[2], label='Defuncion')
Alta = mpatches.Patch(color=Colores[3], label='Alta')
plt.legend(handles=[Amb,Hosp,Def,Alta])
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Estatus en casos femeninos.png')


Aux0 = MasAmb.value_counts()
Aux1 = MasHos.value_counts()
Aux2 = MasDef.value_counts()
Aux3 = MasAlta.value_counts()
NumeroCasos = [Aux0[1],Aux1[1],Aux2[1],Aux3[1]]

plt.figure(figsize=(10, 10))
plt.bar('AMBULATORIO', Aux0[1], label = "Ambulatorio",color=Colores[0])
plt.bar('HOSPITALIZADO', Aux1[1], label = "Hospitalizado",color=Colores[1])
plt.bar('DEFUNCION', Aux2[1], label = "Defuncion",color=Colores[2])
plt.bar('ALTA', Aux3[1], label = "Alta",color=Colores[3])
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Estatus en casos masculinos",y=1.02)
Amb = mpatches.Patch(color=Colores[0], label='Ambulatorio')
Hosp = mpatches.Patch(color=Colores[1], label='Hospitalizado')
Def = mpatches.Patch(color=Colores[2], label='Defuncion')
Alta = mpatches.Patch(color=Colores[3], label='Alta')
plt.legend(handles=[Amb,Hosp,Def,Alta])
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')
plt.savefig('img/Estatus en casos masculinos.png')

Aux0 = OAmb.value_counts()
Aux1 = OHos.value_counts()
Aux2 = ODef.value_counts()
Aux3 = OAlta.value_counts()
x = len(Aux2)
if(x < 2):
    Aux2 = [Aux2[0],0]

   
NumeroCasos = [Aux0[1],Aux1[1],Aux2[1],Aux3[1]]

plt.figure(figsize=(10, 10))
plt.bar('AMBULATORIO', Aux0[1], label = "Ambulatorio",color=Colores[0])
plt.bar('HOSPITALIZADO', Aux1[1], label = "Hospitalizado",color=Colores[1])
plt.bar('DEFUNCION', Aux2[1], label = "Defuncion",color=Colores[2])
plt.bar('ALTA', Aux3[1], label = "Alta",color=Colores[3])
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Estatus en otros generos",y=1.02)
Amb = mpatches.Patch(color=Colores[0], label='Ambulatorio')
Hosp = mpatches.Patch(color=Colores[1], label='Hospitalizado')
Def = mpatches.Patch(color=Colores[2], label='Defuncion')
Alta = mpatches.Patch(color=Colores[3], label='Alta')
plt.legend(handles=[Amb,Hosp,Def,Alta])
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')    
plt.savefig('img/Estatus en otros generos.png')

#Grupos de edades
#-1 Sin datos   # 0 - 1         # 2 - 11
# 12 - 17       # 18 - 24       # 25 - 30
# 31 - 35       # 36 - 40       # 41 - 45
# 46 - 50       # 51 - 55       # 56 - 60
# 61 - 65       # 65    +

Maternal = (DFCasos['Edad'] == 0) | (DFCasos['Edad'] == 1)
Ninos = (DFCasos['Edad'] > 1) & (DFCasos['Edad'] < 12)
Adolescentes = (DFCasos['Edad'] > 11) & (DFCasos['Edad'] < 18)
AdultoJoven = (DFCasos['Edad'] > 17) & (DFCasos['Edad'] < 25)
Adulto1 = (DFCasos['Edad'] > 24) & (DFCasos['Edad'] < 31)
Adulto2 = (DFCasos['Edad'] > 30) & (DFCasos['Edad'] < 36)
Adulto3 = (DFCasos['Edad'] > 35) & (DFCasos['Edad'] < 41)
Adulto4 = (DFCasos['Edad'] > 40) & (DFCasos['Edad'] < 46)
Adulto5 = (DFCasos['Edad'] > 45) & (DFCasos['Edad'] < 51)
Adulto6 = (DFCasos['Edad'] > 50) & (DFCasos['Edad'] < 56)
Adulto7 = (DFCasos['Edad'] > 55) & (DFCasos['Edad'] < 61)
Adulto8 = (DFCasos['Edad'] > 60) & (DFCasos['Edad'] < 66)
Ancianos = (DFCasos['Edad'] > 65)
NODATA = (DFCasos['Edad'] == -1)

Aux0 = Maternal.value_counts()
Aux1 = Ninos.value_counts()
Aux2 = Adolescentes.value_counts()
Aux3 = AdultoJoven.value_counts()
Aux4 = Adulto1.value_counts()
Aux5 = Adulto2.value_counts()
Aux6 = Adulto3.value_counts()
Aux7 = Adulto4.value_counts()
Aux8 = Adulto5.value_counts()
Aux9 = Adulto6.value_counts()
Aux10 = Adulto7.value_counts()
Aux11 = Adulto8.value_counts()
Aux12 = Ancianos.value_counts()
Aux13= NODATA.value_counts()

NumeroCasos = [Aux0[1],Aux1[1],Aux2[1],Aux3[1],Aux4[1],Aux5[1],Aux6[1],Aux7[1],Aux8[1],Aux9[1],Aux10[1],Aux11[1],Aux12[1],Aux13[1]]

plt.figure(figsize=(10, 10))

plt.bar('0-1', Aux0[1],color=Colores[0])
plt.bar('2-11', Aux1[1], color=Colores[1])
plt.bar('12-17', Aux2[1], color=Colores[2])
plt.bar('18-24', Aux3[1], color=Colores[3])
plt.bar('25-30', Aux4[1], color=Colores[4])
plt.bar('31-35', Aux5[1], color=Colores[5])
plt.bar('36-40', Aux6[1],color=Colores[6])
plt.bar('41-45', Aux7[1], color=Colores[7])
plt.bar('46-50', Aux8[1],color=Colores[8])
plt.bar('51-55', Aux9[1],color=Colores[9])
plt.bar('56-60', Aux10[1],color=Colores[10])
plt.bar('61-65', Aux11[1],color=Colores[11])
plt.bar('66+', Aux12[1], color=Colores[12])
plt.bar('Sin Datos', Aux13[1],color=Colores[13])

plt.xlabel("Rangos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos COVID-19 en rangos de edades",y=1.02)
Maternal_p = mpatches.Patch(color=Colores[0], label='0-1')
Ninos_p = mpatches.Patch(color=Colores[1], label='2-11')
Adolescentes_p = mpatches.Patch(color=Colores[2], label='12-17')
AdultoJoven_p = mpatches.Patch(color=Colores[3], label='18-24')
Adulto1_p = mpatches.Patch(color=Colores[4], label='25-30')
Adulto2_p = mpatches.Patch(color=Colores[5], label='31-35')
Adulto3_p = mpatches.Patch(color=Colores[6], label='36-40')
Adulto4_p = mpatches.Patch(color=Colores[7], label='41-45')
Adulto5_p = mpatches.Patch(color=Colores[8], label='46-50')
Adulto6_p = mpatches.Patch(color=Colores[9], label='51-55')
Adulto7_p = mpatches.Patch(color=Colores[10], label='56-60')
Adulto8_p = mpatches.Patch(color=Colores[11], label='61-65')
Ancianos_p = mpatches.Patch(color=Colores[12], label='66+')
nodata_p = mpatches.Patch(color=Colores[13], label='Sin Datos')
plt.legend(handles=[Maternal_p,Ninos_p,Adolescentes_p,AdultoJoven_p,Adulto1_p,Adulto2_p,Adulto3_p,Adulto4_p,Adulto5_p,Adulto6_p,Adulto7_p,Adulto8_p,Ancianos_p,nodata_p],loc='best')
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')    
plt.savefig('img/Casos COVID-19 en rangos de edades.png')



