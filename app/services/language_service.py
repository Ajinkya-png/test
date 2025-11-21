# import logging
# from typing import Tuple

# logger = logging.getLogger(__name__)


# class LanguageService:
#     """
#     Language detection and translation helpers.
#     For production use a robust provider (Google Translate, AWS Translate, etc.).
#     """

#     @staticmethod
#     def detect_language(text: str) -> str:
#         """Naive language detection: returns 'en' for English-like text, else 'unknown'."""
#         if not text:
#             return "unknown"
#         # Very simple heuristic
#         if any(word in text.lower() for word in ["the", "is", "and", "you", "order"]):
#             return "en"
#         return "unknown"

#     @staticmethod
#     def translate(text: str, target_lang: str = "en") -> Tuple[str, str]:
#         """
#         Mock translation: returns (translated_text, detected_source_lang).
#         In prod, call external translate API.
#         """
#         detected = LanguageService.detect_language(text)
#         return (text, detected)


# # app/services/language_service.py
# import logging
# from typing import Dict, Optional
# from enum import Enum

# logger = logging.getLogger(__name__)

# class Language(Enum):
#     ENGLISH = "en"
#     HINDI = "hi" 
#     TAMIL = "ta"

# class LanguageService:
#     """
#     Multi-language support for Food Delivery Voice AI
#     Supports: English, Hindi, Tamil
#     """
    
#     # Translation dictionaries
#     TRANSLATIONS = {
#         Language.ENGLISH: {
#             # Welcome and General
#             "welcome": "Welcome to Food Delivery AI! I can help you order from several categories: Pizza, Burgers, Pasta, or Sushi. What type of food would you like to order?",
#             "fallback": "I didn't hear your order. Please call back to place an order.",
#             "error": "We're experiencing technical difficulties. Please call back later.",
            
#             # Categories
#             "pizza_options": "We have several Pizza options: Margherita for $15.99, Pepperoni for $17.99, Veggie for $16.99, BBQ for $18.99, Hawaiian for $17.49, Meat for $19.99. Which pizza would you like?",
#             "burger_options": "We have several Burgers options: Classic for $12.99, Cheese for $13.99, Bacon for $14.99, Chicken for $13.99, Veggie for $11.99, Double for $16.99. Which burger would you like?",
#             "pasta_options": "We have several Pasta options: Spaghetti for $14.99, Fettuccine for $15.99, Lasagna for $16.99, Penne for $13.99, Ravioli for $15.99, Mac and Cheese for $12.99. Which pasta would you like?",
#             "sushi_options": "We have several Sushi options: California Roll for $18.99, Philadelphia Roll for $19.99, Dragon Roll for $21.99, Rainbow Roll for $22.99, Spicy Tuna for $17.99, Salmon Nigiri for $16.99. Which sushi would you like?",
            
#             # Order Confirmation
#             "item_added": "Excellent choice! {item_name} - {description}. Price: ${price:.2f}. Now I need your delivery address.",
#             "address_prompt": "Please say your complete delivery address including street, city, and zip code.",
            
#             # Address Verification
#             "address_help": "I need your full delivery address including: Street number and name, City, State, and ZIP code. For example: 123 Main Street, New York NY 10001",
#             "address_accepted": "Thank you! Address accepted: {address}. Now proceeding to secure payment.",
#             "address_invalid": "I couldn't verify that address. Please provide a complete delivery address with street, city, and zip code.",
            
#             # Payment
#             "payment_prompt": "Your total is ${amount:.2f}. Say 'confirm payment' to securely process your payment, or 'cancel' to cancel.",
#             "payment_success": "Payment processed successfully! Your {item} order is confirmed. Now notifying the restaurant.",
#             "payment_failed": "Payment system is temporarily unavailable. Please try again later.",
            
#             # Restaurant
#             "restaurant_notified": "Restaurant has accepted your {item} order! Preparation time: 15-20 minutes. Now assigning the best driver for your location.",
#             "restaurant_prompt": "Say 'notify restaurant' to continue.",
            
#             # Driver
#             "driver_assigned": "Driver Michael assigned! He's 4.8 rated and driving a Toyota Corolla. Based on current traffic, your estimated delivery time is {eta} minutes.",
#             "driver_prompt": "Say 'assign driver' to find your delivery partner.",
            
#             # Tracking
#             "tracking_info": "Live tracking update: Your {item} order is being prepared at the restaurant. Driver {driver_name} is on standby and will pick up your order in approximately 5 minutes. You can track the delivery in real-time through our app. We'll send you SMS updates with the live tracking link. Thank you for using our AI-powered food delivery service!",
#             "thank_you": "Thank you for using our service!"
#         },
        
#         Language.HINDI: {
#             # Welcome and General
#             "welcome": "फूड डिलीवरी एआई में आपका स्वागत है! मैं आपकी पिज़्ज़ा, बर्गर, पास्ता, या सुशी ऑर्डर करने में मदद कर सकता हूं। आप किस तरह का खाना ऑर्डर करना चाहेंगे?",
#             "fallback": "मैंने आपका ऑर्डर नहीं सुना। कृपया ऑर्डर देने के लिए वापस कॉल करें।",
#             "error": "हमें तकनीकी समस्या हो रही है। कृपया बाद में कॉल करें।",
            
#             # Categories
#             "pizza_options": "हमारे पास कई पिज़्ज़ा विकल्प हैं: मार्गेरिटा $15.99, पेपरोनी $17.99, वेजी $16.99, बीबीक्यू $18.99, हवाईयन $17.49, मीट लवर्स $19.99। आप कौन सा पिज़्ज़ा चाहेंगे?",
#             "burger_options": "हमारे पास कई बर्गर विकल्प हैं: क्लासिक $12.99, चीज़ $13.99, बेकन $14.99, चिकन $13.99, वेजी $11.99, डबल चीज़ $16.99। आप कौन सा बर्गर चाहेंगे?",
            
#             # Order Confirmation
#             "item_added": "बढ़िया चुनाव! {item_name} - {description}. कीमत: ${price:.2f}. अब मुझे आपका डिलीवरी पता चाहिए।",
#             "address_prompt": "कृपया अपना पूरा डिलीवरी पता बताएं जिसमें सड़क, शहर और ज़िप कोड शामिल हो।",
            
#             # Address Verification
#             "address_help": "मुझे आपका पूरा डिलीवरी पता चाहिए: सड़क नंबर और नाम, शहर, राज्य और ज़िप कोड। उदाहरण: 123 मेन स्ट्रीट, न्यूयॉर्क NY 10001",
#             "address_accepted": "धन्यवाद! पता स्वीकार किया गया: {address}. अब सुरक्षित भुगतान के लिए आगे बढ़ रहे हैं।",
            
#             # Payment
#             "payment_prompt": "आपकी कुल राशि ${amount:.2f} है। भुगतान की पुष्टि करने के लिए 'confirm payment' कहें, या रद्द करने के लिए 'cancel' कहें।",
#             "payment_success": "भुगतान सफलतापूर्वक संसाधित! आपका {item} ऑर्डर कन्फर्म हो गया है। अब रेस्तरां को सूचित किया जा रहा है।",
            
#             # Restaurant
#             "restaurant_notified": "रेस्तरां ने आपका {item} ऑर्डर स्वीकार कर लिया है! तैयारी का समय: 15-20 मिनट। अब आपके स्थान के लिए सबसे अच्छा ड्राइवर नियुक्त किया जा रहा है।",
            
#             # Tracking
#             "tracking_info": "लाइव ट्रैकिंग अपडेट: आपका {item} ऑर्डर रेस्तरां में तैयार किया जा रहा है। ड्राइवर {driver_name} स्टैंडबाय पर है और लगभग 5 मिनट में आपका ऑर्डर उठाएगा। आप हमारे ऐप के माध्यम से डिलीवरी को रियल-टाइम ट्रैक कर सकते हैं। हम आपको लाइव ट्रैकिंग लिंक के साथ एसएमएस अपडेट भेजेंगे। हमारी एआई-पावर्ड फूड डिलीवरी सेवा का उपयोग करने के लिए धन्यवाद!",
#         },
        
#         Language.TAMIL: {
#             # Welcome and General  
#             "welcome": "ஃபூட் டெலிவரி AI-க்கு வரவேற்கிறோம்! நான் பீட்சா, பர்கர், பாஸ்தா அல்லது சுஷி ஆர்டர் செய்ய உதவ முடியும். எந்த வகை உணவை ஆர்டர் செய்ய விரும்புகிறீர்கள்?",
#             "fallback": "உங்கள் ஆர்டரை நான் கேட்கவில்லை. ஆர்டர் செய்ய மீண்டும் அழைக்கவும்.",
#             "error": "நாங்கள் தொழில்நுட்ப சிக்கல்களை எதிர்கொள்கிறோம். தயவு செய்து பின்னர் அழைக்கவும்.",
            
#             # Categories
#             "pizza_options": "எங்களிடம் பல பீட்சா விருப்பங்கள் உள்ளன: மார்கரிட்டா $15.99, பெப்பெரோனி $17.99, வெஜி $16.99, பிபிக்யூ $18.99, ஹவாயியன் $17.49, மீட் லவர்ஸ் $19.99. எந்த பீட்சா வேண்டும்?",
#             "burger_options": "எங்களிடம் பல பர்கர் விருப்பங்கள் உள்ளன: கிளாசிக் $12.99, சீஸ் $13.99, பேகன் $14.99, சிக்கன் $13.99, வெஜி $11.99, டபுள் சீஸ் $16.99. எந்த பர்கர் வேண்டும்?",
            
#             # Order Confirmation
#             "item_added": "அருமையான தேர்வு! {item_name} - {description}. விலை: ${price:.2f}. இப்போது எனக்கு உங்கள் டெலிவரி முகவரி தேவை.",
#             "address_prompt": "தயவு செய்து தெரு, நகரம் மற்றும் ஜிப் கோடு உட்பட உங்கள் முழு டெலிவரி முகவரியையும் சொல்லுங்கள்.",
            
#             # Address Verification  
#             "address_help": "எனக்கு உங்கள் முழு டெலிவரி முகவரி தேவை: தெரு எண் மற்றும் பெயர், நகரம், மாநிலம் மற்றும் ஜிப் கோடு. எடுத்துக்காட்டு: 123 மெய்ன் ஸ்ட்ரீட், நியூயார்க் NY 10001",
#             "address_accepted": "நன்றி! முகவரி ஏற்றுக்கொள்ளப்பட்டது: {address}. இப்போது பாதுகாப்பான கட்டணத்திற்கு செல்கிறோம்.",
            
#             # Payment
#             "payment_prompt": "உங்கள் மொத்த தொகை ${amount:.2f}. பாதுகாப்பாக கட்டணம் செயல்படுத்த 'confirm payment' என்று சொல்லுங்கள், அல்லது ரத்து செய்ய 'cancel' என்று சொல்லுங்கள்.",
#             "payment_success": "கட்டணம் வெற்றிகரமாக செயல்படுத்தப்பட்டது! உங்கள் {item} ஆர்டர் உறுதிப்படுத்தப்பட்டது. இப்போது உணவகத்திற்கு அறிவிக்கப்படுகிறது.",
            
#             # Tracking
#             "tracking_info": "நேரடி டிராக்கிங் புதுப்பிப்பு: உங்கள் {item} ஆர்டர் உணவகத்தில் தயாரிக்கப்படுகிறது. டிரைவர் {driver_name} தயாராக உள்ளார் மற்றும் சுமார் 5 நிமிடங்களில் உங்கள் ஆர்டரை எடுப்பார். எங்கள் ஆப் மூலம் டெலிவரியை நேரடியாக கண்காணிக்க முடியும். நேரடி டிராக்கிங் இணைப்புடன் எஸ்எம்எஸ் புதுப்பிப்புகளை அனுப்புவோம். எங்கள் AI-இயக்கப்பட்ட உணவு விநியோக சேவையைப் பயன்படுத்தியதற்கு நன்றி!",
#         }
#     }
    
#     @staticmethod
#     def detect_language(text: str) -> Language:
#         """
#         Detect language from text input
#         Simple keyword-based detection for demo
#         """
#         text_lower = text.lower()
        
#         # Hindi detection
#         hindi_keywords = ["नमस्ते", "धन्यवाद", "कृपया", "हाँ", "नहीं", "खाना", "पानी"]
#         if any(keyword in text_lower for keyword in hindi_keywords):
#             return Language.HINDI
            
#         # Tamil detection  
#         tamil_keywords = ["வணக்கம்", "நன்றி", "தயவு", "ஆம்", "இல்லை", "உணவு", "தண்ணீர்"]
#         if any(keyword in text_lower for keyword in tamil_keywords):
#             return Language.TAMIL
            
#         # Default to English
#         return Language.ENGLISH
    
#     @staticmethod
#     def get_text(key: str, language: Language, **kwargs) -> str:
#         """
#         Get translated text for a given key and language
#         """
#         try:
#             translation_dict = LanguageService.TRANSLATIONS.get(language, LanguageService.TRANSLATIONS[Language.ENGLISH])
#             text = translation_dict.get(key, LanguageService.TRANSLATIONS[Language.ENGLISH].get(key, key))
            
#             # Format with any provided kwargs
#             if kwargs:
#                 try:
#                     text = text.format(**kwargs)
#                 except KeyError:
#                     logger.warning(f"Missing format keys for {key} in {language}")
            
#             return text
#         except Exception as e:
#             logger.error(f"Translation error for {key} in {language}: {e}")
#             return key



import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class Language(Enum):
    ENGLISH = "en"
    HINDI = "hi" 
    TAMIL = "ta"

class LanguageService:
    """
    Multi-language support for Food Delivery Voice AI
    Supports: English, Hindi, Tamil
    """
    
    # Translation dictionaries
    TRANSLATIONS = {
        Language.ENGLISH: {
            # Welcome and General
            "welcome": "Welcome to Food Delivery AI! I can help you order from several categories: Pizza, Burgers, Pasta, or Sushi. What type of food would you like to order?",
            "fallback": "I didn't hear your order. Please call back to place an order.",
            "error": "We're experiencing technical difficulties. Please call back later.",
            
            # Categories
            "pizza_options": "We have several Pizza options: Margherita for $15.99, Pepperoni for $17.99, Veggie for $16.99, BBQ for $18.99, Hawaiian for $17.49, Meat for $19.99. Which pizza would you like?",
            "burger_options": "We have several Burgers options: Classic for $12.99, Cheese for $13.99, Bacon for $14.99, Chicken for $13.99, Veggie for $11.99, Double for $16.99. Which burger would you like?",
            "pasta_options": "We have several Pasta options: Spaghetti for $14.99, Fettuccine for $15.99, Lasagna for $16.99, Penne for $13.99, Ravioli for $15.99, Mac and Cheese for $12.99. Which pasta would you like?",
            "sushi_options": "We have several Sushi options: California Roll for $18.99, Philadelphia Roll for $19.99, Dragon Roll for $21.99, Rainbow Roll for $22.99, Spicy Tuna for $17.99, Salmon Nigiri for $16.99. Which sushi would you like?",
            
            # Order Confirmation
            "item_added": "Excellent choice! {item_name} - {description}. Price: ${price:.2f}. Now I need your delivery address.",
            "address_prompt": "Please say your complete delivery address including street, city, and zip code.",
            "which_item": "Which {category} would you like?",
            
            # Address Verification
            "address_help": "I need your full delivery address including: Street number and name, City, State, and ZIP code. For example: 123 Main Street, New York NY 10001",
            "address_accepted": "Thank you! Address accepted: {address}. Now proceeding to secure payment.",
            "address_invalid": "I couldn't verify that address. Please provide a complete delivery address with street, city, and zip code.",
            
            # Payment
            "payment_prompt": "Your total is ${amount:.2f}. Say 'confirm payment' to securely process your payment, or 'cancel' to cancel.",
            "payment_success": "Payment processed successfully! Your {item} order is confirmed. Now notifying the restaurant.",
            "payment_failed": "Payment system is temporarily unavailable. Please try again later.",
            
            # Restaurant
            "restaurant_notified": "Restaurant has accepted your {item} order! Preparation time: 15-20 minutes. Now assigning the best driver for your location.",
            "restaurant_prompt": "Say 'notify restaurant' to continue.",
            
            # Driver
            "driver_assigned": "Driver Michael assigned! He's 4.8 rated and driving a Toyota Corolla. Based on current traffic, your estimated delivery time is {eta} minutes.",
            "driver_prompt": "Say 'assign driver' to find your delivery partner.",
            
            # Tracking
            "tracking_info": "Live tracking update: Your {item} order is being prepared at the restaurant. Driver {driver_name} is on standby and will pick up your order in approximately 5 minutes. You can track the delivery in real-time through our app. We'll send you SMS updates with the live tracking link. Thank you for using our AI-powered food delivery service!",
            "thank_you": "Thank you for using our service!"
        },
        
        Language.HINDI: {
            # Welcome and General
            "welcome": "फूड डिलीवरी एआई में आपका स्वागत है! मैं आपकी पिज़्ज़ा, बर्गर, पास्ता, या सुशी ऑर्डर करने में मदद कर सकता हूं। आप किस तरह का खाना ऑर्डर करना चाहेंगे?",
            "fallback": "मैंने आपका ऑर्डर नहीं सुना। कृपया ऑर्डर देने के लिए वापस कॉल करें।",
            "error": "हमें तकनीकी समस्या हो रही है। कृपया बाद में कॉल करें।",
            
            # Categories
            "pizza_options": "हमारे पास कई पिज़्ज़ा विकल्प हैं: मार्गेरिटा $15.99, पेपरोनी $17.99, वेजी $16.99, बीबीक्यू $18.99, हवाईयन $17.49, मीट लवर्स $19.99। आप कौन सा पिज़्ज़ा चाहेंगे?",
            "burger_options": "हमारे पास कई बर्गर विकल्प हैं: क्लासिक $12.99, चीज़ $13.99, बेकन $14.99, चिकन $13.99, वेजी $11.99, डबल चीज़ $16.99। आप कौन सा बर्गर चाहेंगे?",
            "pasta_options": "हमारे पास कई पास्ता विकल्प हैं: स्पेगेटी $14.99, फेटुचिने $15.99, लसगना $16.99, पेन $13.99, रवियोली $15.99, मैक और चीज़ $12.99। आप कौन सा पास्ता चाहेंगे?",
            "sushi_options": "हमारे पास कई सुशी विकल्प हैं: कैलिफोर्निया रोल $18.99, फिलाडेल्फिया रोल $19.99, ड्रैगन रोल $21.99, रेनबो रोल $22.99, स्पाइसी टूना $17.99, सालमन निगिरी $16.99। आप कौन सी सुशी चाहेंगे?",
            
            # Order Confirmation
            "item_added": "बढ़िया चुनाव! {item_name} - {description}. कीमत: ${price:.2f}. अब मुझे आपका डिलीवरी पता चाहिए।",
            "address_prompt": "कृपया अपना पूरा डिलीवरी पता बताएं जिसमें सड़क, शहर और ज़िप कोड शामिल हो।",
            "which_item": "आप कौन सा {category} चाहेंगे?",
            
            # Address Verification
            "address_help": "मुझे आपका पूरा डिलीवरी पता चाहिए: सड़क नंबर और नाम, शहर, राज्य और ज़िप कोड। उदाहरण: 123 मेन स्ट्रीट, न्यूयॉर्क NY 10001",
            "address_accepted": "धन्यवाद! पता स्वीकार किया गया: {address}. अब सुरक्षित भुगतान के लिए आगे बढ़ रहे हैं।",
            "address_invalid": "मैं उस पते को सत्यापित नहीं कर सका। कृपया सड़क, शहर और ज़िप कोड के साथ एक पूरा डिलीवरी पता प्रदान करें।",
            
            # Payment
            "payment_prompt": "आपकी कुल राशि ${amount:.2f} है। भुगतान की पुष्टि करने के लिए 'confirm payment' कहें, या रद्द करने के लिए 'cancel' कहें।",
            "payment_success": "भुगतान सफलतापूर्वक संसाधित! आपका {item} ऑर्डर कन्फर्म हो गया है। अब रेस्तरां को सूचित किया जा रहा है।",
            "payment_failed": "भुगतान प्रणाली अस्थायी रूप से अनुपलब्ध है। कृपया बाद में पुनः प्रयास करें।",
            
            # Restaurant
            "restaurant_notified": "रेस्तरां ने आपका {item} ऑर्डर स्वीकार कर लिया है! तैयारी का समय: 15-20 मिनट। अब आपके स्थान के लिए सबसे अच्छा ड्राइवर नियुक्त किया जा रहा है।",
            "restaurant_prompt": "जारी रखने के लिए 'notify restaurant' कहें।",
            
            # Driver
            "driver_assigned": "ड्राइवर माइकल नियुक्त! उनकी रेटिंग 4.8 है और वह टोयोटा कोरोला चला रहे हैं। वर्तमान ट्रैफिक के आधार पर, आपका अनुमानित डिलीवरी समय {eta} मिनट है।",
            "driver_prompt": "अपने डिलीवरी पार्टनर को खोजने के लिए 'assign driver' कहें।",
            
            # Tracking
            "tracking_info": "लाइव ट्रैकिंग अपडेट: आपका {item} ऑर्डर रेस्तरां में तैयार किया जा रहा है। ड्राइवर {driver_name} स्टैंडबाय पर है और लगभग 5 मिनट में आपका ऑर्डर उठाएगा। आप हमारे ऐप के माध्यम से डिलीवरी को रियल-टाइम ट्रैक कर सकते हैं। हम आपको लाइव ट्रैकिंग लिंक के साथ एसएमएस अपडेट भेजेंगे। हमारी एआई-पावर्ड फूड डिलीवरी सेवा का उपयोग करने के लिए धन्यवाद!",
            "thank_you": "हमारी सेवा का उपयोग करने के लिए धन्यवाद!"
        },
        
        Language.TAMIL: {
            # Welcome and General  
            "welcome": "ஃபூட் டெலிவரி AI-க்கு வரவேற்கிறோம்! நான் பீட்சா, பர்கர், பாஸ்தா அல்லது சுஷி ஆர்டர் செய்ய உதவ முடியும். எந்த வகை உணவை ஆர்டர் செய்ய விரும்புகிறீர்கள்?",
            "fallback": "உங்கள் ஆர்டரை நான் கேட்கவில்லை. ஆர்டர் செய்ய மீண்டும் அழைக்கவும்.",
            "error": "நாங்கள் தொழில்நுட்ப சிக்கல்களை எதிர்கொள்கிறோம். தயவு செய்து பின்னர் அழைக்கவும்.",
            
            # Categories
            "pizza_options": "எங்களிடம் பல பீட்சா விருப்பங்கள் உள்ளன: மார்கரிட்டா $15.99, பெப்பெரோனி $17.99, வெஜி $16.99, பிபிக்யூ $18.99, ஹவாயியன் $17.49, மீட் லவர்ஸ் $19.99. எந்த பீட்சா வேண்டும்?",
            "burger_options": "எங்களிடம் பல பர்கர் விருப்பங்கள் உள்ளன: கிளாசிக் $12.99, சீஸ் $13.99, பேகன் $14.99, சிக்கன் $13.99, வெஜி $11.99, டபுள் சீஸ் $16.99. எந்த பர்கர் வேண்டும்?",
            "pasta_options": "எங்களிடம் பல பாஸ்தா விருப்பங்கள் உள்ளன: ஸ்பகெட்டி $14.99, ஃபெட்டுச்சினே $15.99, லசான்யா $16.99, பென் $13.99, ரவியோலி $15.99, மேக் அண்ட் சீஸ் $12.99. எந்த பாஸ்தா வேண்டும்?",
            "sushi_options": "எங்களிடம் பல சுஷி விருப்பங்கள் உள்ளன: கலிபோர்னியா ரோல் $18.99, ஃபிலடெல்பியா ரோல் $19.99, டிராகன் ரோல் $21.99, ரெயின்போ ரோல் $22.99, ஸ்பைசி டுனா $17.99, சால்மன் நிகிரி $16.99. எந்த சுஷி வேண்டும்?",
            
            # Order Confirmation
            "item_added": "அருமையான தேர்வு! {item_name} - {description}. விலை: ${price:.2f}. இப்போது எனக்கு உங்கள் டெலிவரி முகவரி தேவை.",
            "address_prompt": "தயவு செய்து தெரு, நகரம் மற்றும் ஜிப் கோடு உட்பட உங்கள் முழு டெலிவரி முகவரியையும் சொல்லுங்கள்.",
            "which_item": "எந்த {category} வேண்டும்?",
            
            # Address Verification  
            "address_help": "எனக்கு உங்கள் முழு டெலிவரி முகவரி தேவை: தெரு எண் மற்றும் பெயர், நகரம், மாநிலம் மற்றும் ஜிப் கோடு. எடுத்துக்காட்டு: 123 மெய்ன் ஸ்ட்ரீட், நியூயார்க் NY 10001",
            "address_accepted": "நன்றி! முகவரி ஏற்றுக்கொள்ளப்பட்டது: {address}. இப்போது பாதுகாப்பான கட்டணத்திற்கு செல்கிறோம்.",
            "address_invalid": "அந்த முகவரியை சரிபார்க்க முடியவில்லை. தயவு செய்து தெரு, நகரம் மற்றும் ஜிப் கோடு உட்பட முழு டெலிவரி முகவரியை வழங்கவும்.",
            
            # Payment
            "payment_prompt": "உங்கள் மொத்த தொகை ${amount:.2f}. பாதுகாப்பாக கட்டணம் செயல்படுத்த 'confirm payment' என்று சொல்லுங்கள், அல்லது ரத்து செய்ய 'cancel' என்று சொல்லுங்கள்.",
            "payment_success": "கட்டணம் வெற்றிகரமாக செயல்படுத்தப்பட்டது! உங்கள் {item} ஆர்டர் உறுதிப்படுத்தப்பட்டது. இப்போது உணவகத்திற்கு அறிவிக்கப்படுகிறது.",
            "payment_failed": "கட்டணம் முறை தற்காலிகமாக கிடைக்கவில்லை. தயவு செய்து பின்னர் மீண்டும் முயற்சிக்கவும்.",
            
            # Restaurant
            "restaurant_notified": "உணவகம் உங்கள் {item} ஆர்டரை ஏற்றுக்கொண்டது! தயாரிப்பு நேரம்: 15-20 நிமிடங்கள். இப்போது உங்கள் இடத்திற்கு சிறந்த ஓட்டுநர் நியமிக்கப்படுகிறது.",
            "restaurant_prompt": "தொடர 'notify restaurant' என்று சொல்லுங்கள்.",
            
            # Driver
            "driver_assigned": "ஓட்டுநர் மைக்கேல் நியமிக்கப்பட்டார்! அவரது மதிப்பீடு 4.8 மற்றும் டொயோட்டா கோரோலா ஓட்டுகிறார். தற்போதைய போக்குவரத்தின் அடிப்படையில், உங்கள் மதிப்பிடப்பட்ட டெலிவரி நேரம் {eta} நிமிடங்கள்.",
            "driver_prompt": "உங்கள் டெலிவரி பார்ட்னரைக் கண்டுபிடிக்க 'assign driver' என்று சொல்லுங்கள்.",
            
            # Tracking
            "tracking_info": "நேரடி டிராக்கிங் புதுப்பிப்பு: உங்கள் {item} ஆர்டர் உணவகத்தில் தயாரிக்கப்படுகிறது. டிரைவர் {driver_name} தயாராக உள்ளார் மற்றும் சுமார் 5 நிமிடங்களில் உங்கள் ஆர்டரை எடுப்பார். எங்கள் ஆப் மூலம் டெலிவரியை நேரடியாக கண்காணிக்க முடியும். நேரடி டிராக்கிங் இணைப்புடன் எஸ்எம்எஸ் புதுப்பிப்புகளை அனுப்புவோம். எங்கள் AI-இயக்கப்பட்ட உணவு விநியோக சேவையைப் பயன்படுத்தியதற்கு நன்றி!",
            "thank_you": "எங்கள் சேவையைப் பயன்படுத்தியதற்கு நன்றி!"
        }
    }
    
    @staticmethod
    def detect_language(text: str) -> Language:
        """
        Detect language from text input
        Simple keyword-based detection for demo
        """
        text_lower = text.lower()
        
        # Hindi detection
        hindi_keywords = ["नमस्ते", "धन्यवाद", "कृपया", "हाँ", "नहीं", "खाना", "पानी", "पिज़्ज़ा", "बर्गर", "पास्ता", "सुशी"]
        if any(keyword in text_lower for keyword in hindi_keywords):
            return Language.HINDI
            
        # Tamil detection  
        tamil_keywords = ["வணக்கம்", "நன்றி", "தயவு", "ஆம்", "இல்லை", "உணவு", "தண்ணீர்", "பீட்சா", "பர்கர்", "பாஸ்தா", "சுஷி"]
        if any(keyword in text_lower for keyword in tamil_keywords):
            return Language.TAMIL
            
        # Default to English
        return Language.ENGLISH
    
    @staticmethod
    def get_text(key: str, language: Language, **kwargs) -> str:
        """
        Get translated text for a given key and language
        """
        try:
            translation_dict = LanguageService.TRANSLATIONS.get(language, LanguageService.TRANSLATIONS[Language.ENGLISH])
            text = translation_dict.get(key, LanguageService.TRANSLATIONS[Language.ENGLISH].get(key, key))
            
            # Format with any provided kwargs
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except KeyError:
                    logger.warning(f"Missing format keys for {key} in {language}")
            
            return text
        except Exception as e:
            logger.error(f"Translation error for {key} in {language}: {e}")
            return key