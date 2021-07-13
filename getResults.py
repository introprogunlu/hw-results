import os
import sys
from typing import DefaultDict
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from datetime import date
import json
import csv
from os.path import isdir
from os.path import isfile

def get_repos_results(repo_urls,rooster,auth):
    results = DefaultDict(lambda: [0] * repo_count)
    headers = {
        "Authorization": "token "+auth[1],
        "Content-Type": "application/json"
    }
    for repo_url in repo_urls:
        try:
            # Obtengo las urls de los runs de un actions en un repositorio me quedo la primera y los guardo en workflows_run
            #  REPO  ->* RUNS JOBS(url) ->* Actions
            # Las actions son los conjuntos de acciones automaticas
            # y los runs son cada corrida de de las actions
            resp = requests.request("GET",repo_url+'/actions/runs', headers=headers)
            # print(resp.json()['workflow_runs'][0])
            workflows_run = resp.json()['workflow_runs'][0]['jobs_url']

            # Obtengo los actions de un repositorio con las urls de los jobs obtenidas antes
            resp_wf = requests.request("GET",workflows_run, headers=headers)
            checkruns = resp_wf.json()['jobs'][0]['check_run_url']
            
            # Otengo los resultados de la ultima corrida de las pruebas
            resp_checkruns = requests.request("GET",checkruns, headers=headers)

            #  Obtengo los datos del repo repositorio nombre numero estudiante
            print(repo_url)
            data = repo_url.split('/')[-1].split('-',2)
            if data[2] in rooster:
                student = rooster[data[2]]
            else:
                student = data[2]
            numero_homework = int(data[1])
            points = int(resp_checkruns.json()['output']['summary'].split()[1].split('/')[0])
            # workhome Numero, estudiante, resultado
            print('GUARDAR:',numero_homework,student,points)
            results[student][numero_homework]= points
            # results.append((numero_homework,student,points))
        except:
            print(repo_url)
    return results

def get_repos_names(auth, url, limit_date,sub, hitos):
    repos = []
    params = {'per_page': 100}
    page = 1
    params['page'] = page
    params['sort'] = "created"
    while True:
        params['page'] = page
        print(f'Se van procesando {page} paginas')
        resp = requests.get(url, params=params, auth=auth)
        for repo in resp.json():
            if repo_end_time(repo, hitos) > str(date.today()) or True:
                if repo['created_at'] > limit_date:
                    if repo['url'].find(sub) > 0 :
                        repos.append(repo['url'])
        page +=1    
        if len(resp.json()) == 0 or resp.json()[-1]['created_at'] < limit_date or True:
            break
    return(repos)

load_dotenv()

def repo_end_time(repo, hitos):
    if next((hito for hito in hitos.keys() if hito in repo['html_url']),False):
        return hitos[next((hito for hito in hitos.keys() if hito in repo['html_url']),False)]
    else:
        return '2000-01-01'

def get_results(results_files):
    if isdir(results_files):
        with open (results_files, 'r') as resultFile:
            results = csv.reader(resultFile,delimiter=';')

        results = (results_files)
    else:
        results = []
         
    return results

def get_roosters(roostercsvfile):
    rooster = {}
    with open (roostercsvfile, 'r') as roosterFile:
        csv_content = csv.reader(roosterFile,delimiter=',')
        for student_rooster in csv_content:
            rooster[student_rooster[1]]=student_rooster[0] 
    return rooster

hitos={}
date = datetime.now()

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__,'Hito.json')) as json_file:
    hitos = json.load(json_file)

repos_url = os.getenv('API_ORGANIZATION_URL')
user = os.getenv('GIT_USER')
token= os.getenv('GIT_HUB_TOKEN')
auth = (user, token)
date_limit= os.getenv('START_DATE')
destination = os.getenv('REPOS_DESTINATION')
errors = os.getenv('ERRORS_REPOS')
reposubfix = os.getenv('REPO_SUB')
repo_count = 4
roostercsvfile = os.getenv('ROOSTER_FILE')
results = os.getenv('RESULT_AUTOGRADING')

def main(argv):
    rooster = get_roosters(roostercsvfile)

    result_repos = get_repos_names(auth, repos_url,date_limit, reposubfix, hitos)

    get_results(results)

    results_csv = get_repos_results(result_repos,rooster,auth)
    # print(results_csv)

    jsonString = json.dumps(results_csv)
    jsonFile = open(results+".json", "w")
    jsonFile.write(jsonString)
    jsonFile.close()
if __name__ == "__main__":
   main(sys.argv[1:])


# with open(f'date_clones.ct','w') as testigo:
#     testigo.write(str(date))
