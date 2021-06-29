import os
from numpy.lib.type_check import real
import pandas as pd
from time import sleep


def adjust_per(users_dict,sub_users_dict,X,Y):

    
    for u in users_dict.keys():
        if u in sub_users_dict.keys():
            users_dict[u] = users_dict[u]*X/100 + sub_users_dict[u]/(nav_after- realtime_nav)*Y
        else:
            users_dict[u] = users_dict[u]*X/100 +0/(nav_after- realtime_nav)*Y
    return users_dict




if __name__ == '__main__':
    global base_path, data_path, output_path
    Basic_nav = 580.1 *1000000
    Future_nav = 90 *1000000
    TODAY_NAV = Basic_nav+Future_nav
    base_path = os.getcwd()
    data_path = os.path.join(base_path,'data.xlsx')
    data_df = pd.read_excel(data_path, sheet_name=0, header=0,engine='openpyxl')
    
    
    print('TOTAL in Monney: {}'.format(data_df['Monney'].sum()))
    print('TODAY NAV: {}'.format(TODAY_NAV))
    print('TOTAL Revenue: {}'.format(TODAY_NAV-data_df['Monney'].sum()))

    date_list = list(set(data_df['Date'].tolist()))
    date_list.sort()
    
    #init user dict
    users_dict = {}    
    users_list = list(set(data_df['ClientID'].tolist()))
    for u in users_list:
        users_dict[u] = 0
    
    nav_after = 0

    #MAIN LOOP: loop for all date in data
    for idx,date_ in enumerate(date_list):
        
        sub_users_dict ={}

        sub_data_df = data_df[data_df['Date']==date_list[idx]].reset_index()

        realtime_nav = sub_data_df['RealTimeNAV'][0]
        nav_after = realtime_nav + sub_data_df['Monney'].sum()

        print('{} -- RT: {} -- NAV_AF: {}'.format(date_,realtime_nav,nav_after))

        X = realtime_nav/nav_after*100
        Y = (nav_after- realtime_nav)/nav_after*100

        for u in sub_data_df['ClientID'].tolist():
            sub_users_dict[u] = sub_data_df[sub_data_df['ClientID']==u]['Monney'].sum()

        users_dict = adjust_per(users_dict,sub_users_dict,X,Y)

    #print output
    for u in users_dict.keys():
        print('{} -- {}% -- {} -- {}'.format(u,round(users_dict[u],2),data_df[data_df['ClientID']==u]['Monney'].sum(),round(users_dict[u]*TODAY_NAV/100)))
