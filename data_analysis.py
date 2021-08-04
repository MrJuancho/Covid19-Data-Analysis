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
DFCasos['Edad'] = DFCasos['Edad'].fillna('SIN DATO')
DFCasos['Edad'] = DFCasos['Edad'].replace(regex=[r'(^.*RN.*$)',r'(^.*D.*$)',r'(^.*ME.*$)',r'(^.*d.*$)',r'(^.*m.*$)'], value=0)

DFCasos['Sexo'] = DFCasos['Sexo'].fillna('SIN DATO')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*F.*$)'], value='F')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*M.*$)',r'(^.*H.*$)',r'(^.*N.*$)'], value='M')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*RN.*$)',r'(^.*D.*$)'], value= 0)
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*AÑ.*$)'],value='')

ageinGender = DFCasos['Sexo'].str.findall(r'(^.*[A-Z].*$)')
DFCasos['Sexo'], DFCasos['Edad'] = np.where(ageinGender.isnull() ,[DFCasos['Edad'],DFCasos['Sexo']],[DFCasos['Sexo'],DFCasos['Edad']])

DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*F.*$)'], value='F')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*M.*$)',r'(^.*H.*$)',r'(^.*N.*$)',r'(^.*,M.*$)'], value='M')
DFCasos['Sexo'] = DFCasos['Sexo'].replace(regex=[r'(^.*G.*$)',r'(^.*SN.*$)',r'(^.*X.*$)',r'(^.*R.*$)'], value='OTRO')

DFCasos['Edad'] = DFCasos['Edad'].replace(regex=[r'(^.*M.*$)',r'(^.*H.*$)',r'(^.*N.*$)',r'(^.*,M.*$)'], value='M')
DFCasos['Edad'] = np.where(~DFCasos['Edad'].isin(['M','F','H','NIÑO']),DFCasos['Edad'],'SIN DATO')
DFCasos['Sexo'] = np.where(DFCasos['Sexo'].isin(['M','F','OTRO']),DFCasos['Sexo'],'OTRO')

#Exel de Verificacion de Datos
DFCasos.to_excel('Verificar.xlsx')

#Comenzamos a graficar los datos.

plt.close('all')

#Casos totales analizados por sexo
Sexos = DFCasos['Sexo'].value_counts()
Resultados = DFCasos['Resultado'].value_counts()
Colores = ['#0A1128','#001F54','#034078','#91C4F2','#8CA0D7','#9D79BC','#A14DA0']

DFCasos['Sexo'].value_counts().plot(kind='bar',figsize=(7, 6),rot=0,color=Colores)
plt.xlabel("Genero", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos de Posible Covid por Genero",y=1.02)
fem = mpatches.Patch(color='#0A1128', label='Femenino')
masc = mpatches.Patch(color='#001F54', label='Masculino')
otro = mpatches.Patch(color='#034078', label='Otro')
plt.legend(handles=[fem,masc,otro])
for index,data in enumerate(Sexos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')

plt.figure()
DFCasos['Resultado'].value_counts().plot(kind='bar',figsize=(7, 6),rot=0,color=Colores)
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos Covid-19",y=1.02)
neg = mpatches.Patch(color='#8CA0D7', label='Negativo')
pos = mpatches.Patch(color='#9D79BC', label='Positivo')
sos = mpatches.Patch(color='#A14DA0', label='Sospechoso')
plt.legend(handles=[neg,pos,sos])
for index,data in enumerate(Resultados):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')

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

plt.figure()
plt.bar('Positivos', Aux0[1], label = "Pos")
plt.bar('Negativos', Aux1[1], label = "Neg")
plt.bar('Sospechosos', Aux2[1], label = "Sos")
plt.xlabel("Casos", labelpad=14)
plt.ylabel("Numero de Personas", labelpad=14)
plt.title("Casos en genero Femenino",y=1.02)
for index,data in enumerate(NumeroCasos):
    plt.text(x=index, y =data+1, s=f"{data}", fontdict=dict(fontsize=12),ha='center')

plt.show()
#plt.figure()
#plt.plot.bar(,DFCasos['Sexo'])

""" mx = gpd.read_file('mapa_mexico/')\
        .set_index('CLAVE')\
        .to_crs(epsg=4485)
print(mx.head()) """
