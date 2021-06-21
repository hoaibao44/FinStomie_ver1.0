import os
import json
import requests
import ast
from math import ceil
from datetime import datetime,timedelta,timezone
from web_utils.get_driver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import string
from xlwings import Book
import pandas as pd
from time import sleep

import yaml


def make_folder(folders):
    for folder in folders:
        os.makedirs(folder,exist_ok=True)

# ↓↓↓↓↓↓↓↓↓↓↓↓↓ func for Timeline  ↓↓↓↓↓↓↓↓↓↓↓↓↓ 
def get_raw_timeline(cookies_txt_path,acc_id):
    cookies = ast.literal_eval(json.load(open(cookies_txt_path, 'r', encoding='utf-8'))) #DRAFTED   
    page_id = 1
    final_pandas = pd.DataFrame()
    while True:
        
        get_tl_data_url = "https://manager.line.biz/api/bots/@{}/timeline/drafts/list?page={}".format(acc_id,page_id)
        response = requests.get(get_tl_data_url, headers=headers, cookies=cookies)
        
        if response.status_code == 200:
            response_text = response.content.decode(encoding='utf-8').replace("\u3000"," ")
            sbig_response = json.loads(response_text)
            
            # check if has no info then break
            if len(sbig_response['drafts'])==0:
                break

            sub_out_pandas =pd.io.json.json_normalize(sbig_response['drafts'])
            sub_out_pandas['key'] = sub_out_pandas['post_info.id']
            media_pandas =pd.DataFrame()
            for i in range(0,len(sub_out_pandas)):
                sub_pandas  = pd.io.json.json_normalize(sub_out_pandas['contents.media'][i])
                sub_pandas['key'] = sub_out_pandas['post_info.id'][i]
                media_pandas = media_pandas.append(sub_pandas)

            sub_out_pandas = pd.merge(sub_out_pandas,media_pandas,how='outer')
        
        final_pandas =final_pandas.append(sub_out_pandas)
        page_id+=1
        
    final_pandas.to_csv(os.path.join(raw_path,"{}_{}_raw_data.csv".format(acc_id,'TL')),encoding='utf-16',sep='\t',index=False)

# ↓↓↓↓↓↓↓↓↓↓↓↓↓ func for messages  ↓↓↓↓↓↓↓↓↓↓↓↓↓ 
def filter_needcheck_ms(cookies_txt_path,acc_id,start_date,end_date):

    cookies = ast.literal_eval(json.load(open(cookies_txt_path, 'r', encoding='utf-8'))) #DRAFTED   
    get_ms_data_url = "https://manager.line.biz/api/bots/@{}/broadcasts?status=DRAFTED&page={}&count=50&from={}&to={}&isSearch=true".format(
        acc_id, 1, int(datetime.strptime(start_date, '%Y/%m/%d').timestamp()), int(datetime.strptime(end_date, '%Y/%m/%d').timestamp()))
    response = requests.get(get_ms_data_url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        response_text = response.content.decode(encoding='utf-8').replace("\u3000"," ")
        sbig_response = json.loads(response_text)
        if sbig_response['total'] != 0:
            print("FUNC: filter_needcheck_ms -- DONE --> Return to MAIN")
            return pd.io.json.json_normalize(sbig_response,'list')['id'].tolist()
        else:
            print("FUNC: filter_needcheck_ms -- 0 msg --> Return to MAIN")
            return []
    else:
        print("FUNC: filter_needcheck_ms -- FAIL to connect to server --> Return to MAIN")
        return []

def get_rich_info(cookies_txt_path,acc_id,origin_id):
    rich_url = "https://manager.line.biz/api/bots/@{}/richImage/{}".format(acc_id,origin_id)
    cookies = ast.literal_eval(json.load(open(cookies_txt_path, 'r', encoding='utf-8')))    
    response = requests.get(rich_url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        response_text = response.content.decode(encoding='utf-8').replace("\u3000"," ")
        sbig_response = json.loads(response_text)
        out_pandas = pd.io.json.json_normalize(sbig_response,max_level=0)

        miniPandas = pd.DataFrame()
        for idx,key in enumerate(sbig_response['contents'].keys()):
            if idx ==0:
                myPandas =pd.io.json.json_normalize(sbig_response['contents'][key])
                myPandas['type'] = key
                miniPandas = myPandas
            else:
                myPandas =pd.io.json.json_normalize(sbig_response['contents'][key])
                myPandas['type'] = key
                miniPandas = pd.merge(miniPandas,myPandas,how='outer')
        out_pandas = out_pandas.assign(key=1).merge(miniPandas.assign(key=1),how='outer')
        del out_pandas['contents'],out_pandas['key']

        out_pandas.to_csv(os.path.join(raw_path,'{}_{}_RICH_data.csv'.format(acc_id,origin_id)),encoding='utf-16',sep='\t', index=False)
        print("FUNC: get_rich_info_new -- DONE --> Return to MAIN")
    else:
        print("FUNC: get_rich_info_new -- FAIL to connect to server --> Return to MAIN")

def get_flex_info(cookies_txt_path,acc_id,origin_id):
    flex_url = "https://manager.line.biz/api/bots/@{}/cardTypeMessages/{}".format(acc_id,origin_id)
    cookies = ast.literal_eval(json.load(open(cookies_txt_path, 'r', encoding='utf-8')))    
    response = requests.get(flex_url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        response_text = response.content.decode(encoding='utf-8').replace("\u3000"," ")
        sbig_response = json.loads(response_text)
        actions_pandas = pd.io.json.json_normalize(sbig_response['message']['actions'],max_level=1)
        actions_pandas['key'] =actions_pandas['cardNumber']

        origin_pandas = pd.io.json.json_normalize(sbig_response['message']['origin']['messages'])
        origin_pandas['key'] = origin_pandas.index.to_list()
        
        actions_pandas = pd.merge(origin_pandas,actions_pandas,how='outer')
        actions_pandas['key'] = 1

        #pd.io.json.json_normalize(sbig_response['message']['origin'],'messages',record_prefix='origin_msg_') #this is for origin: has img url
        out_pandas = pd.io.json.json_normalize(sbig_response)
        out_pandas = out_pandas.assign(key=1).merge(actions_pandas,how='outer')
        
        del out_pandas['message.actions'], out_pandas['message.origin.title'], out_pandas['message.origin.messages'], out_pandas['message.origin.viewmore.images']

        out_pandas.to_csv(os.path.join(raw_path,'{}_{}_FLEX_data.csv'.format(acc_id,origin_id)),encoding='utf-16',sep='\t', index=False)
        print("FUNC: get_flex_info_new -- DONE --> Return to MAIN")
    else:
        print("FUNC: get_flex_info_new -- FAIL to connect to server --> Return to MAIN")

def get_ms_data(cookies_txt_path,acc_id,ms_id):
    ms_url = 'https://manager.line.biz/api/bots/@{}/broadcasts/{}'.format(acc_id,ms_id)
    cookies = ast.literal_eval(json.load(open(cookies_txt_path, 'r', encoding='utf-8')))    
    #print(ms_url)
    #print(cookies)
    response = requests.get(ms_url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        print("FUNC: get_ms_data_new -- request OK --> starting split response data")
        response_text = response.content.decode(encoding='utf-8').replace("\u3000"," ")
        sbig_response = json.loads(response_text)
        big_df = pd.io.json.json_normalize(sbig_response)
        del big_df['balloons'],big_df['messageIds']
        
        sballoon_response = json.loads(response_text)['balloons'][0]
        smessageID_response = json.loads(response_text)['messageIds'][0]
        for idx, balloon in enumerate(sballoon_response):
                            
            #get actions for RICH
            if balloon['contentType'] == 'RICH':
                #actions_pandas = pd.io.json.json_normalize(balloon['messageObject'],'actions',record_prefix='rich_acctions_').assign(key=balloon['key'])
                #out_pandas = out_pandas.merge(actions_pandas,how='outer')
                #print("https://manager.line.biz/api/bots/@{}/richImage/{}".format(acc_id,balloon['originalId']))
                get_rich_info(cookies_txt_path,acc_id,balloon['originalId'])
            #get actions for FLEX
            elif balloon['contentType'] == 'FLEX':
                #print("https://manager.line.biz/api/bots/@{}/cardTypeMessages/{}".format(acc_id,balloon['originalId']))
                get_flex_info(cookies_txt_path,acc_id,balloon['originalId'])
            else:
                pass 

            if idx ==0:
                out_pandas = pd.io.json.json_normalize(balloon)
                out_pandas['messageIds'] = smessageID_response[idx]
                
            else:
                balloon_df = pd.io.json.json_normalize(balloon)
                balloon_df['messageIds'] = smessageID_response[idx]
                out_pandas =   pd.concat([out_pandas,balloon_df], ignore_index=True)

        out_pandas = out_pandas.assign(key=1).merge(big_df.assign(key=1), how='outer', on='key')

        #del pandas's col 
        del_col =['updateToken','messageObject.contents.contents','messageObject.actions']
        for col in del_col:
            if out_pandas.columns.tolist().count(col) > 0:
                del out_pandas[col]

        out_pandas.to_csv(os.path.join(raw_path,'{}_{}_MS_data.csv'.format(acc_id,ms_id)),encoding='utf-16',sep='\t',index=False)

        print("FUNC: get_ms_data_new -- DONE --> Return to MAIN")
    else:
        print("FUNC: get_ms_data_new -- FAIL to connect to server --> Return to MAIN")

def MS_data_processing(acc_id,ms_id):

    in_file_path = os.path.join(raw_path+"\\{}_{}_MS_data.csv".format(acc_id,ms_id))
    in_column_setting = os.path.join(base_path,"columns\\メッセージ.csv")
    
    in_pandas = pd.read_csv(in_file_path,encoding='utf-16',sep='\t')
    columns_df = pd.read_csv(in_column_setting,encoding='shift_jis',sep=',')
    area_pandas = pd.read_excel(os.path.join(base_path, 'columns\\IN_info_data.xlsx'), sheet_name=0, header=0)

    for i in range(0,len(in_pandas)):
        if in_pandas['messageObject.altText'].isnull()[i]: #isnull() sample
            in_pandas['messageObject.altText'][i] = in_pandas['text'][i]

    out_pandas = pd.DataFrame()
    for i in range(0,len(columns_df['OUT'].tolist())):
        if in_pandas.columns.to_list().count(columns_df['IN'].tolist()[i]) > 0:
            out_pandas[columns_df['OUT'].tolist()[i]] = in_pandas[columns_df['IN'].tolist()[i]]
        else:
            out_pandas[columns_df['OUT'].tolist()[i]] = None

    all_flex = pd.DataFrame()
    all_rich = pd.DataFrame()
    for i in range(0,len(out_pandas)):
        out_pandas['配信日時(時刻)'][i] = datetime.fromtimestamp(out_pandas['配信日時(時刻)'][i],timezone(timedelta(hours=+9))).strftime('%H:%M')
        out_pandas['配信日時'][i] = datetime.fromtimestamp(out_pandas['配信日時'][i],timezone(timedelta(hours=+9))).strftime('%Y/%m/%d')
        out_pandas['作成日時'][i] = datetime.fromtimestamp(out_pandas['作成日時'][i],timezone(timedelta(hours=+9))).strftime('%Y/%m/%d %H:%M')
        #for age:
        age_list ={'in_age': ['15-19', '20-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-'],
        'out_age': ['15～19歳', '20～24歳', '25～29歳', '30～34歳', '35～39歳', '40～44歳', '45～49歳', '50歳以上']
        }
        for j in range(0,len(age_list['in_age'])):
            out_pandas['年齢'][i] = out_pandas['年齢'][i].replace(age_list['in_age'][j],age_list['out_age'][j])

        #for 性別
        gen_list ={
            'in_gen':['f','m'],
            'out_gen':['女性','男性']
        }
        for j in range(0,len(gen_list['in_gen'])):
            out_pandas['性別'][i] = out_pandas['性別'][i].replace(gen_list['in_gen'][j],gen_list['out_gen'][j])
        #for is-with-timeline
        
        #for area
        for j in range(0,len(area_pandas)):
            out_pandas['エリア'][i] = out_pandas['エリア'][i].replace(area_pandas['Code_2'][j],area_pandas['Name'][j])

        #for include+exclude
        operators = ast.literal_eval(out_pandas['オーディエンス含める'][i])
        include, exclude = "",""
        for ope in operators:
            if ope['operator'] == 'INCLUDE':
                include += ope['description']+", "
            elif ope['operator'] == 'EXCLUDE' :
                exclude += ope['description']+", "
            else:
                pass
        out_pandas['オーディエンス含める'][i] =include[:-2]
        out_pandas['オーディエンス除外する'][i] =exclude[:-2]

        #msg link
        out_pandas['編集画面URL'][i] = 'https://manager.line.biz/account/@{}/broadcast/edit/{}'.format(acc_id,ms_id)

        #flag
        out_pandas['作成別フラグ'][i] = '{}_{}'.format(ms_id,str(i+1))

        if out_pandas['広告タイプ'][i] == 'RICH':
            if i==0:                
                all_rich = rich_processing(acc_id,out_pandas['オリジナルID'][i])
            else:
                all_rich =pd.concat([all_rich,rich_processing(acc_id,out_pandas['オリジナルID'][i])])
        elif out_pandas['広告タイプ'][i] == 'FLEX':
            if i==0:
                all_flex= flex_processing(acc_id,out_pandas['オリジナルID'][i])
            else:
                all_flex =pd.concat([all_flex,flex_processing(acc_id,out_pandas['オリジナルID'][i])])
    
    if len(all_flex) !=0:
        all_flex['オリジナルタイプ'] ='FLEX'
        all_flex['アカウントID'] =acc_id
        all_flex.to_csv(os.path.join(process_path,"{}_{}_FLEX_data.csv".format(acc_id,ms_id)),encoding='utf-16',sep='\t',index=False)
    
    if len(all_rich) != 0:
        all_rich['オリジナルタイプ'] ='RICH'
        all_rich['アカウントID'] = acc_id
        all_rich.to_csv(os.path.join(process_path,"{}_{}_RICH_data.csv".format(acc_id,ms_id)),encoding='utf-16',sep='\t',index=False)
    
    out_pandas['アカウントID'] = acc_id
    out_pandas.to_csv(os.path.join(process_path,"{}_{}_MS_data.csv".format(acc_id,ms_id)),encoding='utf-16',sep='\t',index=False)
    print("FUNC: MS_data_processing -- DONE --> Return to MAIN")

def rich_processing(acc_id,origin_id):
    #read in_data: raw_rich file & cl change file
    in_pandas = pd.read_csv(os.path.join(raw_path,'{}_{}_RICH_data.csv'.format(acc_id,round(float(origin_id)))),encoding='utf-16',sep='\t')
    columns_df = pd.read_csv(os.path.join(base_path,"columns\\RICH.csv"),encoding='shift_jis',sep=',')
    
    #start building out pandas
    out_pandas = pd.DataFrame()
    for i in range(0,len(columns_df['OUT'].tolist())):
        if in_pandas.columns.to_list().count(columns_df['IN'].tolist()[i]) > 0:
            out_pandas[columns_df['OUT'].tolist()[i]] = in_pandas[columns_df['IN'].tolist()[i]]
        else:
            out_pandas[columns_df['OUT'].tolist()[i]] = None

    # replace masters
    type_replace_list ={'A':'1','B':'2','C':'3','D':'4','E':'5','F':'6','G':'7','H':'8'}

    # for each row, change output data-form
    for i in range(0,len(out_pandas)):
        out_pandas['作成日'][i] = datetime.fromtimestamp(int(out_pandas['作成日'][i]),timezone(timedelta(hours=+9))).strftime('%Y/%m/%d %H:%M')

        #replace area
        for key in type_replace_list.keys():
            out_pandas['コンテンツタイプ'][i] = str(out_pandas['コンテンツタイプ'][i]).replace(type_replace_list[key],key)


    #out_pandas.to_csv(os.path.join(process_path,'{}_{}_RICH_data.csv'.format(acc_id,round(float(origin_id)))),encoding='utf-16',sep='\t',index=False)
    
    print("FUNC: rich_processing -- DONE --> Return to MS_data_processing")
    return out_pandas

def flex_processing(acc_id,origin_id):
    #read in_data: raw_rich file & cl change file
    in_pandas = pd.read_csv(os.path.join(raw_path,'{}_{}_FLEX_data.csv'.format(acc_id,round(float(origin_id)))),encoding='utf-16',sep='\t')
    columns_df = pd.read_csv(os.path.join(base_path,"columns\\FLEX.csv"),encoding='shift_jis',sep=',')
    
    #start building out pandas
    out_pandas = pd.DataFrame()
    for i in range(0,len(columns_df['OUT'].tolist())):
        if in_pandas.columns.to_list().count(columns_df['IN'].tolist()[i]) > 0:
            out_pandas[columns_df['OUT'].tolist()[i]] = in_pandas[columns_df['IN'].tolist()[i]]
        else:
            out_pandas[columns_df['OUT'].tolist()[i]] = None
    
    for i in range(0,len(out_pandas)):
        out_pandas['作成日'][i] = datetime.fromtimestamp(int(out_pandas['作成日'][i])/1000,timezone(timedelta(hours=+9))).strftime('%Y/%m/%d %H:%M')
        out_pandas['編集日'][i] = datetime.fromtimestamp(int(out_pandas['編集日'][i])/1000,timezone(timedelta(hours=+9))).strftime('%Y/%m/%d %H:%M')
        out_pandas['カード番号'][i] = str(out_pandas['カード番号'][i]).replace("-1","もっと見るカード")
        #take img url
        if out_pandas['イメージURL'].isnull().tolist()[i] == False:
            try:
                out_pandas['イメージURL'][i] = ast.literal_eval(str(out_pandas['イメージURL'][i]))[0]['src']
            except:
                pass

    #out_pandas.to_csv(os.path.join(process_path,'{}_{}_FLEX_data.csv'.format(acc_id,round(float(origin_id)))),encoding='utf-16',sep='\t',index=False)
    print("FUNC: flexprocessing -- DONE --> Return to MS_data_processing")
    return out_pandas

if __name__ == '__main__':
    """=============================================
    1/ global var & setting for output folder's path
    ========================================-========"""
    global raw_path,process_path,output_path,header
    
    headers = {
        'authority': 'manager.line.biz',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'ja',
    }

    #base_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    if os.path.isfile(os.path.join(os.getcwd(),'__pythonFunc\\run.txt')):
        base_path = open(os.path.join(os.getcwd(),'__pythonFunc\\run.txt'), 'r').read().strip()
    else:
        base_path = os.getcwd()
    print('=========\n'+base_path+'\n=========')

    today_date = datetime.now()
    today_date_string = 'Output_'+ today_date.strftime("%Y%m%d")  # check hereeee   

    raw_path = os.path.join(base_path,today_date_string+"\\raw")
    process_path = os.path.join(base_path,today_date_string+"\\process")
    output_path = os.path.join(base_path,today_date_string+"\\output")
    #make process folder
    folders= [raw_path,process_path,output_path]
    make_folder(folders)

    
    """=============================================
    2/ read config file: get account-id 
    ================================================"""  
    config_df = pd.read_excel(os.path.join(base_path ,'LOA_ezCheck_ver1.0.xlsm'), sheet_name=0, header=2)

    #try:
    
    # loop: all raw of config_df
    for i in range(0, len(config_df)):
        json_path = config_df['アイパス格納先'][i]
        login_email_id = json_path.replace(".json","").split("\\")[-1]
        acc_id = config_df['アカウントID'][i]
        
        print("\n================\nMAIN: STARTING --【{}】{}".format(i,acc_id))
        account_url = "https://manager.line.biz/account/@{}".format(acc_id)
        start_date = config_df['作成期間対象(はじめ)'][i].strftime("%Y/%m/%d") #int(today_date.timestamp())
        end_date = config_df['作成期間対象(おわり)'][i].strftime("%Y/%m/%d")

        cookies_txt_path = os.path.join(base_path, 'cookies\\cookies_for_{}.txt'.format(login_email_id))
        # check if already has cookies then skip opening chrome: cookies file path == cookies_txt_path
        # or cookies file is generate more than 1 days before
        if os.path.isfile(cookies_txt_path) == False or datetime.fromtimestamp(os.path.getmtime(cookies_txt_path)+86400).strftime("%Y%m%d%H%M") <= datetime.now().strftime("%Y%m%d%H%M") :
            print("MAIN: start loging in to get cookies --")
            line_driver = WebDriver(download_dir=os.path.join(base_path, 'download'),
                                    exe_path=os.path.join(base_path,'chromedriver.exe'))

            infos = json.load(open(json_path, 'r', encoding='utf-8'))
            #infos ={"ID":"cyberagent0123@gmail.com","パスワード":"ca1227"}

            login_id = infos['ID']
            login_pass = infos['パスワード']

            line_driver.driver.get('https://manager.line.biz/logout')
            line_driver.driver.get('https://manager.line.biz/')
            
            line_driver.safe_click_element_by_xpath("//a[text()='ビジネスアカウントでログイン']")
            line_driver.safe_send_keys_element_by_xpath("//input[@name='email']", login_id)
            line_driver.safe_send_keys_element_by_xpath("//input[@name='password']", login_pass + Keys.RETURN)

            sleep(4)

            #print(hello)

            line_driver.driver.get(account_url)

            account_name = line_driver.get_element_by_xpath("//div[@id='header-user']").text.split()[0]

            cookies = {
                "_gid": line_driver.driver.get_cookie("_gid")['value'],
                "_ga": line_driver.driver.get_cookie("_ga")['value'],
                "ses": line_driver.driver.get_cookie("ses")['value']
            }

            #write cookies 
            with open(cookies_txt_path, mode='w') as f:
                f.write('"'+str(cookies)+'"')

            line_driver.quit()
        else:
            print("MAIN: already has cookies file")
        
        # get list of need-check msg: output = a list of ms_id(s)
        ms_ids = filter_needcheck_ms(cookies_txt_path,acc_id,start_date,end_date)
        print("MAIN: total need-check msg: {}".format(len(ms_ids)))

        # for each ms_id, get data: output = none, file is saved into [raw] folder
        for ms_id in ms_ids:
            # STEP1: DL
            print("\nMAIN: get ms_data, ms_id = {}".format(ms_id))
            if os.path.isfile(os.path.join(raw_path+"\\{}_{}_MS_data.csv".format(acc_id,ms_id))) == False:
                get_ms_data(cookies_txt_path,acc_id,ms_id)
            else:
                print("MAIN: already has raw-file")

            # STEP2: Prcessing
            if os.path.isfile(os.path.join(process_path+"\\{}_{}_MS_data.csv".format(acc_id,ms_id))) == False:
                MS_data_processing(acc_id,ms_id)
            else:
                print("MAIN: already has processing-file")


        #STEP3: all ms to one file
        for data_type in ['MS','FLEX','RICH']:
            out_pandas = pd.DataFrame()
            for idx,ms_id in enumerate(ms_ids):
                #concat all MS file of this acc
                file_path = os.path.join(process_path+"\\{}_{}_{}_data.csv".format(acc_id,ms_id,data_type))
                if os.path.isfile(file_path) != False:
                    minipandas = pd.read_csv(file_path,encoding='utf-16',sep='\t')
                    if idx==0:
                        out_pandas =minipandas
                    else:
                        out_pandas = pd.concat([out_pandas,minipandas])
            out_pandas = out_pandas.drop_duplicates()
            out_pandas.to_csv(os.path.join(output_path,"{}_{}_All_data.csv".format(acc_id,data_type)),encoding='utf-16',sep='\t',index=False)

    """
        root = tk.Tk()
        root.withdraw()
        #messagebox.showinfo('完了', '完了しました。') 
    
    except:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('エラー', 'エラーが発生しました。')    
    """
