import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_family_alert(risk, message):
    topic = os.getenv('NTFY_TOPIC')

    if not topic:
        print('Family alert not sent: NTFY_TOPIC is missing.')
        return False

    try:
        response = requests.post(
            f'https://ntfy.sh/{topic}',
            data=message.encode('utf-8'),
            headers={
                'Title': 'Scam Guardian Warning',
                'Priority': 'high'
            },
            timeout=10
        )

        response.raise_for_status()
        print('Family alert sent successfully.')
        return True

    except requests.RequestException as error:
        print(f'Could not send family alert: {error}')
        return False