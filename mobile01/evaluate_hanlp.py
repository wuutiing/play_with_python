'''
@author    : wuutiing@outlook.com
@date      : 2020-03-14
@comments  : 
# requirements
hanlp

'''



import os
import hanlp
import random
import json

# PKU_NAME_MERGED_SIX_MONTHS_CONVSEG 这个预训练模型比较合适

def evaluate(result_path='logs'):
    strings = []
    choices = random.choices(range(len(os.listdir('datas'))), k=10)
    for idx, p in enumerate(os.listdir('datas')):
        if idx in choices:
            strings.append(json.load(open('datas/'+p))['dialogues']['1']['content'])

    for key in hanlp.pretrained.ALL:
        print(key)
        try:
            tokenizer = hanlp.load(key)
            for idx, string in enumerate(strings):
                f = open(f'{result_path}/{idx}.txt', 'a')
                f.write(f'>>>>>\n{key}\n{" ".join(tokenizer(string))}\n')
        except:
            pass
    

        
