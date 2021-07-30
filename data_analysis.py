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
                        'Signos y sintomas':df2.iloc[:,9],
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

DFCasos['Resultado'] = DFCasos['Resultado'].fillna('SOSPECHOSO')
DFCasos['Resultado'] = DFCasos['Resultado'].replace(regex=[r'^POS.*', r'^´POS.*'], value='POSITIVO')
DFCasos['Resultado'] = DFCasos['Resultado'].replace(regex=[r'^NEG.*'], value='NEGATIVO')
DFCasos['Resultado'] = DFCasos['Resultado'].replace(regex=[r'^IN.*', r'^´NO.*',r'M.*',r'NO.*',r'PEN.*',r'REC.*',r'SIN.*'], value='SOSPECHOSO')

#Conversion de datos correspondientes

#DFCasos= DFCasos.convert_dtypes().dtypes

#Organizar los datos por Columna

DFResultados = pd.DataFrame([DFCasos['Resultado'],DFCasos['Fecha Result']]).transpose()
#DFResultados = np.where(DFResultados['Resultado']==DFResultados['Fecha Result'],[DFResultados['Fecha Result'],DFResultados['Resultado']],[DFResultados['Resultado'],DFResultados['Fecha Result']])
print(DFResultados)


DFCasos.to_excel('Verificar.xlsx')
#DFEdad = DFCasos['']
