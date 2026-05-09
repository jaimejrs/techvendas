import pandas as pd
import data_loader

engine = data_loader._get_engine()
with engine.connect() as conn:
    print("rh.funcionario:")
    print(pd.read_sql("SELECT * FROM rh.funcionario LIMIT 5", conn))
    print("\ngeral.pessoa:")
    print(pd.read_sql("SELECT * FROM geral.pessoa LIMIT 5", conn))
