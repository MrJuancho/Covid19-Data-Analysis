import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

archive = pd.ExcelFile('RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx')
df1 = pd.read_excel(archive,"RED NEGATIVA")
df2 = pd.read_excel(archive,"SEGUIMIENTO DE CASOS COVID 19")
head =df1.head() 
print(head)