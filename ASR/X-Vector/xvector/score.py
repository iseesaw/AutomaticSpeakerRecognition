# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import json
import h5py

dirpath = 'D:\\VMware\\Share\\CrossDeviceSR\\database\\af2019-sr-devset-20190312\\'
def line2arr(line):

    items = line.split('  ')

    speaker = items[0].split('-')[0]
    uttr = items[0].split('-')[1]
    v = items[1].split(' ')[1:-1]
    arr = np.array(v, dtype=float)
    #print(speaker, uttr)
    return uttr, arr

def cosin(v1, v2):

    return np.dot(v1,v2)/(np.linalg.norm(v1)*(np.linalg.norm(v2)))

def read():
    with open('xvector.txt', 'r') as f:
        lines = f.read().split('\n')

    uttr_vector = {}

    for line in lines:
        if len(line) < 512:
            continue
        
        uttr, vector = line2arr(line)
        
        uttr_vector[uttr] = vector

    return uttr_vector

def write_h5(vector, file):
    f = h5py.File('data/{}.h5'.format(file), 'w')
    f['xvector'] = vector
    f.close()
    
def read_h5(key):
    f = h5py.File('data/{}.h5'.format(key), 'r')
    vector = f['xvector'][:]   
    f.close()
    return vector

def load_json(file):
    with open(file, 'r') as f:
        dic = json.load(f)
    return dic

def enroll(groupid, uttr_vector):
    group = 'group{}'.format(groupid)

    enroll_list = load_json(dirpath + 'enroll.json')

    for key in enroll_list[group].keys():
        #print('enrolling {}...'.format(key))
        vectors = []
        for file in enroll_list[group][key]['FileID']:
            vector = uttr_vector[file]
            vectors.append(vector)
        vectors = np.asarray(vectors)
        write_h5(np.mean(vectors, axis=0), key)

def compute(vector, group, enroll_list):
    dis = []
    for key in enroll_list[group].keys():
        v = read_h5(key)
        dis.append(cosin(vector, v))

    return np.mean(np.asarray(dis), axis=0)

def test(groupid, uttr_vector):
    group = 'group{}'.format(groupid)

    enroll_list = load_json(dirpath + 'enroll.json')
    test_list = load_json(dirpath + 'test.json')

    dis = []
    for key in test_list[group].keys():
        #print('testing {}...'.format(key))
        vector = uttr_vector[key]
        dis.append(compute(vector, group, enroll_list))

    for i in range(0, 10):
        score(dis, group, test_list, i)

def score(dis, group, test_list, threshold=0):
    annota_dic = load_json(dirpath + 'annotation.json')

    sps, imss, segs, scos= [], [], [], []
    s = 0
    for sco, seg in zip(dis, test_list[group].keys()):
        speaker = annota_dic[group][seg]['SpeakerID']
        ism = annota_dic[group][seg]['isMember']
        sps.append(speaker)
        imss.append(ism)
        segs.append(seg)
        scos.append(sco)
        if sco > threshold*0.1 and ism=='Y':
            s += 1
        if sco < threshold*0.1 and ism=='N':
            s += 1
    print('{:.1f}'.format(threshold*0.1),s/len(sps))
    if threshold == 0:
        pd.DataFrame(data={
            'SpeakerID': sps,
            'isMember':imss,
            'FileID':segs,
            'Score': scos,
            }).to_csv('result.csv')

uttr_vector = read()
for i in range(6):
    print('==================== {} ====================='.format(i))
    enroll(i, uttr_vector)
    test(i, uttr_vector)
