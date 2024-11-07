import requests
import jenkins

def get_jenkins_crumb(jenkins_url, user, password):
    response = requests.get(f'{jenkins_url}/crumbIssuer/api/json', auth=(user, password))
    if response.status_code == 200:
        data = response.json()
        return {data['crumbRequestField']: data['crumb']}
    else:
        print(f'Failed to get crumb: {response.status_code} {response.reason}')
        return None

def generate_api_token(jenkins_url, user, password):
    """
    Generiert ein neues Jenkins API-Token für den angegebenen Benutzer.
    """
    groovy_script = f'''
    import jenkins.security.ApiTokenProperty
    import hudson.security.User

    def user = User.get('{user}')
    def apiTokenProperty = user.getProperty(ApiTokenProperty.class)

    def result = apiTokenProperty.tokenStore.generateNewToken('automation-token')
    println(result.plainValue)
    '''

    crumb = get_jenkins_crumb(jenkins_url, user, password)
    if not crumb:
        print('Failed to get Jenkins crumb. Cannot proceed.')
        return None

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    headers.update(crumb)

    data = {'script': groovy_script}

    response = requests.post(f'{jenkins_url}/scriptText', auth=(user, password), headers=headers, data=data)

    if response.status_code == 200:
        api_token = response.text.strip()
        print(f'Generated API Token: {api_token}')
        return api_token
    else:
        print(f'Failed to generate API token: {response.status_code} {response.reason}')
        return None

class CrumbRequester(jenkins.Requester):
    """
    Angepasster Requester, der Jenkins Crumb zu jeder Anfrage hinzufügt.
    """

    def __init__(self, username, password, baseurl, ssl_verify=True):
        super().__init__(username=username, password=password, baseurl=baseurl, ssl_verify=ssl_verify)
        self.crumb = None

    def get_crumb(self):
        response = requests.get(f'{self.baseurl}/crumbIssuer/api/json', auth=(self.username, self.password), verify=self.ssl_verify)
        if response.status_code == 200:
            data = response.json()
            self.crumb = (data['crumbRequestField'], data['crumb'])
        else:
            raise Exception(f'Failed to get crumb: {response.status_code} {response.reason}')

    def request(self, method, url, **kwargs):
        if self.crumb is None:
            self.get_crumb()
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'][self.crumb[0]] = self.crumb[1]
        return super().request(method, url, **kwargs)
