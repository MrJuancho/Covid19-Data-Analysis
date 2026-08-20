import pandas as pd

df = pd.read_excel('RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx', sheet_name='SEGUIMIENTO DE CASOS COVID 19', usecols="A:T", skiprows=range(0,13))

df.describe()

# archive = pd.ExcelFile('RED-NEGATIVA-COVID-02_VIGILANCIA-HOSPITALARIA 11.01.21.xlsx')



# df2 = pd.read_excel(archive,"SEGUIMIENTO DE CASOS COVID 19",usecols="A:T",skiprows=range(0,13))