import json
import time
import traceback
import requests


def load_environmental_variables():
    with open('config.py') as f:
        environment_vars = json.load(f)

    bot_id = environment_vars['BOT_KEY']

    user_list = [
        environment_vars['REZI_ID'],
        environment_vars['DOK_ID']
    ]

    return bot_id, user_list


def campsite_is_available(j, campsite, park):
    if (
        j['campsites'][campsite]['availabilities']['2022-05-27T00:00:00Z'] == 'Available'
        or j['campsites'][campsite]['availabilities']['2022-05-28T00:00:00Z'] == 'Available'
    ):
        return True


def main():
    bot_id, user_list = load_environmental_variables()

    campground_ids = {
        '232447': 'Yosemite',  # Upper Pines
        '232449': 'Yosemite',  # North Pines
        '232450': 'Yosemite',  # Lower Pines
        # '272266': 'Zion',
        # '232445': 'Zion'
    }

    last_checked = 0
    offset = 0
    try:
        while True:
            if time.time() > last_checked + 60*30:
                for id in campground_ids.keys():
                    print('checking campsite')
                    r = requests.get(
                        f'https://www.recreation.gov/api/camps/availability/campground/{id}/month?start_date=2022-05-01T00%3A00%3A00.000Z',
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
                        }
                    )
                    j = r.json()
                    print('hit rec.gov api')
                    camp_count = 0

                    if j.get('campsites'):
                        for campsite in j.get('campsites'):
                            if camp_count >= 3:
                                break
                            if campsite_is_available(j, campsite, campground_ids[id]):
                                print(j['campsites'][campsite]['availabilities'])
                                print(f'{campground_ids[id]}: {j["campsites"][campsite]["loop"]} AVAILABLE')
                                for user_id in user_list:
                                    param = {
                                        'chat_id': user_id,
                                        'text': f'<a href="https://www.recreation.gov/camping/campsites/{campsite}">{campground_ids[id]}: {j["campsites"][campsite]["loop"]} AVAILABLE</a>',
                                        'parse_mode': 'HTML',
                                        'disable_web_page_preview': True
                                    }
                                    requests.post(
                                        f'https://api.telegram.org/bot{bot_id}/sendMessage',
                                        data=param
                                    )
                                camp_count += 1

                    if camp_count == 0:
                        print(f'No open campsites found for {id}')

                last_checked = time.time()

            new_messages = requests.post(
                f'https://api.telegram.org/bot{bot_id}/getUpdates?offset={offset}'
            ).text
            print('getting messages')
            new_messages = json.loads(new_messages)['result']
            allowed_types = [
                'message',
                'edited_message',
            ]
            for message_type in allowed_types:
                for message in new_messages:
                    if message.get(message_type):
                        if message[message_type].get('text') == '/bing' or message[message_type].get('text') == '/bing':
                            param = {
                                    'chat_id': message[message_type]['chat']['id'],
                                    'text': 'bong',
                                    'parse_mode': 'HTML',
                            }
                            requests.post(
                                f'https://api.telegram.org/bot{bot_id}/sendMessage',
                                data=param
                            )
                            print('bong\'d')
            if new_messages:
                offset = new_messages[-1]['update_id'] + 1

            time.sleep(120)

    except Exception as e:
        print(f'{time.time()}: {e}')
        # print(locals())
        param = {
                'chat_id': user_list[0],
                'text': f'Wolf Crash...\n{traceback.format_exc()}\n{e}',
                'parse_mode': 'HTML',
        }
        requests.post(
            f'https://api.telegram.org/bot{bot_id}/sendMessage',
            data=param
        )


if __name__ == '__main__':
    main()
