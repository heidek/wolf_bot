from pandas import date_range
import json
import time
import traceback
import requests


class WolfForeman:
    '''
    Handler for workers
    '''
    worker_list = []

    def __init__(self):
        self.bot_id, self.user_list = self.load_environmental_variables()

    def load_environmental_variables(self):
        with open('config.py') as f:
            environment_vars = json.load(f)

        bot_id = environment_vars['BOT_KEY']

        user_list = [
            environment_vars['REZI_ID'],
            environment_vars['DOK_ID']
        ]

        return bot_id, user_list

    def add_worker(self, worker):
        self.worker_list.append(worker)

    def run_workers(self):
        for worker in self.worker_list:
            worker.run()

    def send_message(self, message, user_id):
        param = {
            'chat_id': user_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        requests.post(
            f'https://api.telegram.org/bot{self.bot_id}/sendMessage',
            data=param
        )


class CampChecker:
    '''
    Checks given campsite for availability on start_date. If an end_date is given, checks availability from start_date to end_date
    '''
    last_checked = 0

    def __init__(self, campground_id, start_date, end_date=None,):
        self.campground_id = campground_id
        self.start_date = start_date
        self.end_date = end_date

        if not self.end_date:
            self.end_date = self.start_date

    def campsite_is_available(self, j, campsite):
        dates = date_range(self.start_date, self.end_date)
        return all([j['campsites'][campsite]['availabilities'][f'{d.strftime("%Y-%m-%d")}T00:00:00Z'] == 'Available' for d in dates])

    def run(self):
        if self.last_checked == 0 or time.time() > self.last_checked + 60*30:
            # Make this a function
            r = requests.get(
                f'https://www.recreation.gov/api/camps/availability/campground/{self.campground_id}/month?start_date=2022-05-01T00%3A00%3A00.000Z',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
                }
            )
            j = r.json()

            print('hit api')
            camp_count = 0
            if j.get('campsites'):
                for campsite in j.get('campsites'):
                    if camp_count > 3:
                        break
                    if self.campsite_is_available(j, campsite):
                        camp_count += 1
                        print(f'{j["campsites"][campsite]["loop"]} AVAILABLE')
                        for user in WolfForeman().user_list:
                            WolfForeman().send_message(
                                self,
                                f'<a href="https://www.recreation.gov/camping/campsites/{campsite}"> {j["campsites"][campsite]["loop"]} AVAILABLE</a>',
                                user
                            )

            if camp_count == 0:
                print(f'No sites found at {self.campground_id}')

            self.last_checked = time.time()


class BingBong:
    '''
    Ping function
    '''
    chat_offset = 0
    allowed_message_types = [
        'message',
        'edited_message',
    ]

    def get_messages(self):
        new_messages = requests.post(
            f'https://api.telegram.org/bot{WolfForeman().bot_id}/getUpdates?offset={self.chat_offset}'
        ).text
        print('getting messages')
        new_messages = json.loads(new_messages)['result']

        if new_messages:
            self.chat_offset = new_messages[-1]['update_id'] + 1

        return new_messages

    def run(self):
        new_messages = self.get_messages()

        for message_type in self.allowed_message_types:
            for message in new_messages:
                if message.get(message_type):
                    if message[message_type].get('text') == '/bing' or message[message_type].get('text') == '/bing':
                        WolfForeman().send_message('bong', message[message_type]['chat']['id'])
                        print('bong\'d')


def main():
    mr_wolf = WolfForeman()
    wolf_workers = [
        CampChecker('232447', '2022-05-27', '2022-05-28'),  # Upper Pines Wolf
        CampChecker('232449', '2022-05-27', '2022-05-28'),  # North Pines Wolf
        CampChecker('232450', '2022-05-27', '2022-05-28'),  # Lower Pines Wolf
        CampChecker('232781', '2022-05-21'),  # Hume Wolf
        BingBong(),
    ]
    for worker in wolf_workers:
        mr_wolf.add_worker(worker)

    try:
        while True:
            mr_wolf.run_workers()

            time.sleep(120)

    except Exception as e:
        print(f'{time.time()}: {e}')
        # print(locals())
        param = {
                'chat_id': WolfForeman().user_list[0],  # Rezi
                'text': f'Wolf Crash...\n{traceback.format_exc()}\n{e}',
                'parse_mode': 'HTML',
        }
        requests.post(
            f'https://api.telegram.org/bot{WolfForeman().bot_id}/sendMessage',
            data=param
        )


if __name__ == '__main__':
    main()
