import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import re
import datetime

archive = pd.ExcelFile('RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx')
#df1 = pd.read_excel(archive,"RED NEGATIVA",usecols = "B:N",skiprows =range(0,7))
df2 = pd.read_excel(archive,"SEGUIMIENTO DE CASOS COVID 19",usecols="A:T",skiprows=range(0,13))

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

DFCasos['Fecha Result'] = DFCasos['Fecha Result'].fillna('01/01/2000  12:00:00 a. m.')

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
#Si necesitamos cambiar casos en los que no se parezca a ciertos datos aplicacmos 'np.where(DFCasos['Resultado'].isin(['POSITIVO','NEGATIVO','SOSPECHOSO']),DFCasos['Resultado'],'SOSPECHOSO')'

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
DFCasos['Sexo'] = np.where(DFCasos['Sexo'].isin(['M','F','OTRO']),DFCasos['Sexo'],'SIN DATO')

#ageinGender = DFCasos['Sexo'].str.findall(r'(^.*[0-9].*$)')
#DFCasos['Resultado'] = np.where(DFCasos['Resultado'].isin(['M','F','0']),DFCasos['Resultado'],'OTRO')

DFCasos.to_excel('Verificar.xlsx')