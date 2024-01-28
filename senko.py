import urequests
import uhashlib


class Senko:
    raw = "https://raw.githubusercontent.com"
    github = "https://github.com"
#    print('user', user,'repo',REPOSITORY,'url',GITHUB_URL,'files',files,'headers',headers)
#    print('Setup Senko Class')
#    def __init__(self, USER, REPOSITORY, url=None, branch="master", working_dir="app", files=["test1.py", "test2.py"], headers={}):
#        """Senko OTA agent class.

#    def __init__(self, user, repo, url=None, branch="main", working_dir="app", files=["test1.py", "test2.py"], headers={}):
#    def __init__(self, user, repo, url=None, files=["test1.py", "test2.py"], headers={}):
##    def __init__(self, user, repo, url, files=["test1.py", "test2.py"], headers={}):
    def __init__(self, url, user, repo, branch, files, headers={}):          
        print('Enter OTA initialisation routine')
#    def __init__(self, user, repo, url=None, branch="main", files=["test1.py", "test2.py"], headers={}):
        """Senko OTA agent class.

        Args:
            user (str): GitHub user.
            repo (str): GitHub repo to fetch.
            branch (str): GitHub repo branch. (master)
            working_dir (str): Directory inside GitHub repo where the micropython app is.
            url (str): URL to root directory.
            files (list): Files included in OTA update.
            headers (list, optional): Headers for urequests.
        """
##        self.base_url = "{}/{}/{}".format(url, user, repo, branch) if user else url.replace(self.github, self.raw)
        self.base_url = "{}/{}/{}/{}".format(self.raw, user, repo, branch) if user else url.replace(self.github, self.raw)
#        self.base_url = "{}/{}/{}".format(self.github, user, repo) if user else url.replace(self.github, self.raw)
#        print('self.base_url: ',self.base_url)
#        self.url = url if url is not None else "{}/{}/{}".format(self.base_url)
#       self.url = self.base_url
#        self.url = url if url is not None else "{}/{}/{}".format(self.base_url, branch, working_dir)
        self.url =  "{}/{}/{}/{}".format(self.github, user, repo, branch) if user else url.replace(self.github, self.raw)
#        self.url = url if url is not None else "{}/{}/{}".format(self.base_url, branch)
#        print('self.url: ',self.url)
        self.headers = headers
#        print('self.headers: ',self.headers)
        self.files = files
        print('Exit OTA initialisation routine. Files to check for OTA updates: ',self.files)
#        print('Are the URLs correct ?')

    def _check_hash(self, x, y):
        x_hash = uhashlib.sha1(x.encode())
        y_hash = uhashlib.sha1(y.encode())

        x = x_hash.digest()
        y = y_hash.digest()

        if str(x) == str(y):
            print('No updated file available.')
            return True
        else:
            return False

    def _get_file(self, url):
#        print('Enter _get_file routine. self.base_url: ', self.base_url)
        payload = urequests.get(url, headers=self.headers)
#        print('Payload: ',payload)
        code = payload.status_code
        print('Payload status code (if 200, file was found): ',code, 'Payload = file content: ')
        print(payload.text)
        print('')
#        input('_get_file routine faultfinding. If Status code = 200, file found.')
        if code == 200:
#            print('File was found.') #,file)
            return payload.text
        else:
            print('File was not found.')
            return None

    def _check_all(self):
        changes = []
        print('Find updated files on Github')
#        print('self.base_url: ', self.base_url)
#        input('Wait before proceeding in _check_all routine for updated files.')
        for file in self.files:
            print('Out of files: ',self.files, 'check file: ',file)
#            latest_version = self._get_file(self.url + "/" + file)
            latest_version = self._get_file(self.base_url + "/" + file)
            print('Latest_version on Github: ')
            print(latest_version)
            print('')
#            input('Temp WAIT in _check_all routine')
            if latest_version is None:
                print('No, there is no updated version')
                continue
            
            try:
                print('File: ',file)
                with open(file, "r") as local_file:
                    local_version = local_file.read()
            except:
                local_version = ""

            if not self._check_hash(latest_version, local_version):
                print('There are changes in file: ',file)
                changes.append(file)
            
#            input('#####  Goto next file    #####')
        
        print('End of finding updated files. Changes found in file(s):',changes)
#        input('exit Check_All routine')
        return changes

    def fetch(self):
        """Check if newer version is available.

        Returns:
            True - if is, False - if not.
        """
        if not self._check_all():
            return False
        else:
            return True

    def update(self):
        """Replace all changed files with newer one.

        Returns:
            True - if changes were made, False - if not.
        """
        print('Enter OTA file update routine.')
        changes = self._check_all()

#        print('Changes from Update routine:',changes)
#        print('self.base_url: ',self.base_url)
#        print('self.url: ',self.url)
#        print('####  Wait before Updating  ####')
        for file in changes:
            print('File: ',file)
            with open(file, "w") as local_file:
                print('Local_file: ',local_file,'####  Go to _get_file routine   ####')
                local_file.write(self._get_file(self.base_url + "/" + file))
                
                print('File written')

        if changes:
            print('Changes made')
            return True
        else:
#            print('NO Changes made')
            return False
