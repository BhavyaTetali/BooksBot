import logging
import requests
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

GOOGLE_BOOKS_API_KEY=""  # set google books api key here.


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def close(session_attributes, fulfillment_state, message, responseCard):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message,
            'responseCard': responseCard,
        }
    }

    return response


""" --- Functions that control the bot's behavior --- """


def get_books_list(intent_request):
    search_term = get_slots(intent_request)["SearchTerm"]

    res = requests.get(
        'https://www.googleapis.com/books/v1/volumes?q=' + search_term + '&key=' + GOOGLE_BOOKS_API_KEY)
    json_res = json.loads(res.text)

    response_cards = {
        "version": 1,
        "contentType": "application/vnd.amazonaws.card.generic",
        "genericAttachments": [
            {
                "subTitle": "Click it to check the buying options",
                "buttons": []
            }
        ]
    }

    # create set to avoid duplicate books from the result.
    books_set = set()

    content = 'These are a few suggestions. \n'
    count = 1
    for item in json_res["items"]:
        book_title = item["volumeInfo"]["title"]
        if book_title in books_set:
            # if title already exists in set then skip it.
            continue;
        books_set.add(book_title)
        if count > 5:
            break
        
        full_book_title = item["volumeInfo"]["title"] 
                #    + ", by " + item["volumeInfo"]["authors"][0]
                
        if "subtitle" in item["volumeInfo"]:
            full_book_title = full_book_title + " : " + item["volumeInfo"]["subtitle"]

        content = content + str(count) + ") " +  full_book_title + "; \n"

        itemkey = "intitle:" + item["volumeInfo"]["title"]  + "+inauthor:" + item["volumeInfo"]["authors"][0]
        
        response_cards["genericAttachments"][0]["buttons"].append(
            {"text": str(count), "value": "get price for " + itemkey})
        count = count + 1
        
    print(response_cards)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': content},
                 response_cards
                 )

def get_price(intent_request):
    search_term = get_slots(intent_request)["BookDetails"]

    res = requests.get(
        'https://www.googleapis.com/books/v1/volumes?q=' + search_term + '&key=' + GOOGLE_BOOKS_API_KEY)
    print(search_term)
    json_res = json.loads(res.text)
    print(res.text)

    response_cards = {
        "version": 1,
        "contentType": "application/vnd.amazonaws.card.generic",
        "genericAttachments": [
            {
                "title": "",
                "subTitle": "",
                "buttons": [
                    {
                        "text": "Check other book",
                        "value": "I want to read a book",
                    },
                    {
                        "text": "I'm done",
                        "value": "Adios!",
                    },
                    
                ]
            }
        ]
    }
    
    full_book_title = ""
    if len(json_res["items"]) > 0:
        item = json_res["items"][0]
        full_book_title = item["volumeInfo"]["title"]
        if "subtitle" in item["volumeInfo"]:
            full_book_title = full_book_title + " : " + item["volumeInfo"]["subtitle"]

        attachment = response_cards["genericAttachments"][0]
        attachment["title"] = "Authors : " + (', '.join(item["volumeInfo"]["authors"]))
        
        attachment["subTitle"] = "Free"
        if "saleInfo" in item and "listPrice" in item["saleInfo"]:
            listPrice = item["saleInfo"]["listPrice"]
            attachment["subTitle"] = str(listPrice["amount"]) + " " + str(listPrice["currencyCode"])
        
        attachment["imageUrl"] = item["volumeInfo"]["imageLinks"]["thumbnail"]
        
        
    print(response_cards)
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': full_book_title},
                 response_cards
                 )


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'SearchKey':
        return get_books_list(intent_request)
    
    if intent_name == 'GetPrice':
        return get_price(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)


