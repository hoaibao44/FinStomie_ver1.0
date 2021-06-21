import numpy as np
import pandas as pd


if __name__ == "__main__":
    i=1
    final_array =[]
    while True:
        if len(final_array)==270:
            break
        
        np.random.seed(i)
        out_array = []
        while True:
            if len(out_array) == 24:
                break
            
            ran_num = np.random.randint(1,76)
            if ran_num not in out_array:
                out_array.append(ran_num)
        
        if out_array not in final_array:
            final_array.append(out_array)
        i+=1

    print(final_array)

    pd.DataFrame(final_array).to_excel("ahaha.xlsx",index=False)