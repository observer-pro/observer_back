import json
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel


class Block(BaseModel):
    type_: list | str | None
    properties: dict | list | None


async def scrape(domain: str, page_id: str) -> dict[str, str]:
    """
    Scrapes data from a Notion page using the Notion API.

    Args:
        domain (str): The domain of the Notion workspace.
        page_id (str): The ID of the page to scrape.
    Returns:
        dict[str, str]: The scraped data if successful, or an error dictionary if unsuccessful.
    """
    url = f'https://{domain}/api/v3/loadPageChunk'
    payload = {
        "page": {
            "id": page_id,
        },
        "limit": 50,
        "cursor": {
            "stack": [],
        },
        "chunkNumber": 0,
        "verticalColumns": False,
    }
    try:
        async with aiohttp.ClientSession() as session:  # noqa SIM117
            async with session.post(
                    url, data=json.dumps(payload), headers={'Content-Type': 'application/json'},
            ) as response:
                if response.status == 200:
                    return await response.json()
                return {
                    "error": f'Could not connect to Notion, status: {response.status}, reason: {response.reason}',
                }
    except Exception:
        return {"error": f'Could not connect to Notion to parse tasks with id: {page_id}!'}


def extract_domain_and_page_id_from_url(url: str) -> dict[str, str]:
    """
    Extract the domain and page ID from a given URL.

    Args:
        url (str): The URL from which to extract domain and page ID.

    Returns:
        dict[str, str]: A dictionary with the extracted domain and page ID, or
            a dictionary with an error message if the page_id length is not 32 symbols, or
            a dictionary with an error message if the url is not valid.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path_parts = url.split("/")[1:]

        if '?' in path_parts[2]:  # noqa SIM108
            page_id = path_parts[2].split('?')[0][-32:]
        else:
            page_id = path_parts[2][-32:]

        if len(page_id) != 32:
            return {'message': f'Could not extract page_id from url: {url}, page_id length is not 32 symbols'}

        page_id = page_id[:8] + '-' + page_id[8:12] + '-' + page_id[12:16] + '-' + page_id[16:20] + '-' + page_id[20:]
        return {'domain': domain, 'page_id': page_id}
    except Exception:
        return {'message': f'Could not extract domain and page_id from url: {url}'}


async def parse_exercises(data: dict) -> list[str]:
    """
    Parse the exercises from the given data dictionary.

    Args:
        data (dict): The data dictionary containing exercise blocks.

    Returns:
        list[str]: The parsed exercises as a list of strings.
    """
    filtered_data: list[Block] = [
        Block(type_=item['type'], properties=item.get('properties', {}))
        for item in [
            data['block'][block]['value']
            for block in data['block']
            if (
                    'properties' in data['block'][block]['value'] and
                    data['block'][block]['value'].get('type') != 'page' or
                    data['block'][block]['value'].get('type') == 'divider'
            )
        ]
    ]
    all_tasks = []
    task = []
    for item in filtered_data:
        if 'header' in item.type_:
            task.append(
                '<h3>' + item.properties['title'][0][0] + '</h3>',
            )
        elif 'code' in item.type_:
            task.append(
                '<pre class="ql-syntax">' + item.properties['title'][0][0] + '</pre>',
            )
        elif item.type_ == 'divider':
            all_tasks.append(''.join(task))
            task = []
        else:
            text = []
            for i in item.properties['title']:
                if isinstance(i, str):
                    text.append(i)
                else:
                    text.append(i[0])
            task.append(''.join(text) + '<br>')

    all_tasks.append(''.join(task))
    return all_tasks


async def get_exercises_from_notion(link: str) -> list[str] | dict[str, str]:
    """
    Get exercises from a Notion page given a link.

    Args:
        link (str): The link to the Notion page.

    Returns:
        A list of exercise strings if successful, or a dictionary with an error message if unsuccessful.
    """
    extracted_data = extract_domain_and_page_id_from_url(link)
    domain = extracted_data.get('domain')
    page_id = extracted_data.get('page_id')

    if domain and page_id:
        data: dict = await scrape(domain, page_id)
        if data.get('error'):
            return {'message': data.get('error')}
        records = data.get('recordMap')
        return await parse_exercises(records)
    return {'message': f'Could not extract domain and page_id from url: {link}'}
