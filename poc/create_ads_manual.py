"""Создание объявлений вручную"""
from api_client import DirectAPIClient

c = DirectAPIClient()
GROUP_ID = 5704219166

# Объявление 2
ad2 = c.create_text_ad(
    ad_group_id=GROUP_ID,
    title='Kubectl через чат',
    title2='AI видит логи и чинит',
    text='Делегируй рутину ИИ. Подключи кластер, дебажь через чат.',
    href='https://execai.ru/'
)
print(f'Ad 2: {ad2}')

# Объявление 3  
ad3 = c.create_text_ad(
    ad_group_id=GROUP_ID,
    title='GPT-5 и Claude для DevOps',
    title2='Без VPN, оплата картой РФ',
    text='Топовые модели и SSH интеграция. Управляй инфрой через чат.',
    href='https://execai.ru/'
)
print(f'Ad 3: {ad3}')

print('\nГотово! Объявления созданы.')

