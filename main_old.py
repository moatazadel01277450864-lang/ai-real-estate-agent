import os
import json
from datetime import datetime

import requests
from dotenv import load_dotenv
from google import genai


# ============================================================
# إعدادات المشروع
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY غير موجود في ملف .env")


client = genai.Client(api_key=API_KEY)


GOOGLE_SHEETS_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzotzZVjnuSW3JCgckoy2NN0uqTHB7b1ypJj86xOB2QgoE4y7iTYc1e9TqAx-1uZZcs"
    "/exec"
)


# ============================================================
# تعليمات AI Agent
# ============================================================

SYSTEM_INSTRUCTION = """
أنت وكيل مبيعات ذكي لشركة عقارات.

مهمتك:

1. التحدث مع العميل باللغة العربية بشكل طبيعي ومحترم.
2. فهم احتياج العميل.
3. استخراج كل البيانات التي ذكرها العميل في المحادثة.
4. الاحتفاظ بالبيانات التي عرفتها من الرسائل السابقة وعدم فقدها.
5. عدم اختراع أي عقار أو سعر أو مشروع أو معلومة غير مؤكدة.
6. إذا كانت معلومات العميل ناقصة، اسأل عن المعلومات المهمة تدريجيًا.
7. تحديد حالة العميل.
8. تحديد درجة اهتمام العميل من 0 إلى 100.
9. تحديد البيانات الناقصة.
10. استخدام قاعدة بيانات العقارات المرسلة إليك عند البحث عن عقار مناسب.
11. لا تعرض للعميل أي عقار على أنه متاح إلا إذا كان موجودًا في قاعدة البيانات.
12. إذا لم تجد عقارًا مناسبًا في قاعدة البيانات، أخبر العميل بذلك بوضوح ولا تخترع بديلًا.

حالات العميل:

- new = عميل جديد
- interested = مهتم
- qualified = عميل محتمل مؤهل
- customer = عميل حالي
- not_interested = غير مهتم

البيانات المطلوبة:

- name
- phone
- area
- budget
- property_type
- rooms
- payment_method
- delivery_time

قواعد مهمة:

- لا تخترع بيانات غير موجودة.
- احتفظ بالمعلومات التي سبق أن ذكرها العميل.
- الرد الذي يراه العميل يجب أن يكون طبيعيًا ومختصرًا ومفيدًا.
- لا تعرض بيانات التحليل الداخلية للعميل.
- عند وجود عقار مناسب في قاعدة البيانات، يمكنك اقتراحه للعميل.
- استخدم السعر والمنطقة ونوع العقار والغرف وطريقة الدفع وموعد التسليم كما هي في قاعدة البيانات.
"""


# ============================================================
# شكل البيانات التي يرجعها Gemini
# ============================================================

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string",
            "description": "الرد الذي سيراه العميل"
        },
        "status": {
            "type": "string",
            "enum": [
                "new",
                "interested",
                "qualified",
                "customer",
                "not_interested"
            ]
        },
        "interest_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100
        },
        "customer_data": {
            "type": "object",
            "properties": {
                "name": {
                    "type": ["string", "null"]
                },
                "phone": {
                    "type": ["string", "null"]
                },
                "area": {
                    "type": ["string", "null"]
                },
                "budget": {
                    "type": ["string", "null"]
                },
                "property_type": {
                    "type": ["string", "null"]
                },
                "rooms": {
                    "type": ["string", "null"]
                },
                "payment_method": {
                    "type": ["string", "null"]
                },
                "delivery_time": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "name",
                "phone",
                "area",
                "budget",
                "property_type",
                "rooms",
                "payment_method",
                "delivery_time"
            ]
        },
        "missing_data": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "reply",
        "status",
        "interest_score",
        "customer_data",
        "missing_data"
    ]
}


# ============================================================
# تحميل العقارات من Google Sheets
# ============================================================

def get_properties_from_sheet():

    response = requests.get(
        GOOGLE_SHEETS_URL,
        timeout=15
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise ValueError(
            "تعذر قراءة العقارات: " + str(result)
        )

    return result.get("properties", [])


# ============================================================
# إرسال رسالة إلى Gemini
# ============================================================

def send_message(
    message,
    properties,
    previous_interaction_id=None
):

    properties_text = json.dumps(
        properties,
        ensure_ascii=False
    )

    request_data = {
        "model": "gemini-3.6-flash",

        "input": f"""
رسالة العميل:

{message}


قائمة العقارات المتاحة حاليًا من قاعدة البيانات:

{properties_text}


استخدم قائمة العقارات فقط عند اقتراح عقار.

لا تخترع عقارًا أو سعرًا أو أي معلومة غير موجودة في القائمة.


إذا وجدت عقارًا مناسبًا:

- اذكر العقار المناسب بشكل طبيعي.
- استخدم بياناته الحقيقية من القائمة.


إذا لم يوجد عقار مناسب:

- أخبر العميل أنه لا يوجد تطابق حاليًا.
- لا تخترع أي عقار بديل.


لا تعرض قائمة العقارات كاملة للعميل إلا إذا كان ذلك ضروريًا.
""",

        "system_instruction": SYSTEM_INSTRUCTION,

        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": RESPONSE_SCHEMA
        }
    }

    if previous_interaction_id:
        request_data["previous_interaction_id"] = (
            previous_interaction_id
        )

    return client.interactions.create(
        **request_data
    )


# ============================================================
# حفظ الـ Lead في Google Sheets
# ============================================================

def save_lead_to_sheet(data):

    now = datetime.now()

    customer_data = data.get(
        "customer_data",
        {}
    )

    payload = {
        "date": now.strftime("%Y-%m-%d"),

        "time": now.strftime("%H:%M:%S"),

        "name": customer_data.get("name") or "",

        "phone": customer_data.get("phone") or "",

        "area": customer_data.get("area") or "",

        "budget": customer_data.get("budget") or "",

        "property_type": (
            customer_data.get("property_type") or ""
        ),

        "rooms": customer_data.get("rooms") or "",

        "payment_method": (
            customer_data.get("payment_method") or ""
        ),

        "delivery_time": (
            customer_data.get("delivery_time") or ""
        ),

        "status": data.get("status") or "",

        "interest_score": data.get(
            "interest_score",
            ""
        ),

        "notes": ""
    }

    response = requests.post(
        GOOGLE_SHEETS_URL,
        json=payload,
        timeout=15
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# تحديد هل العميل يستحق التسجيل أم لا
# ============================================================

def should_save_lead(data):

    customer_data = data.get(
        "customer_data",
        {}
    )

    phone = customer_data.get("phone")

    status = data.get("status")

    if phone:
        return True

    if status == "qualified":
        return True

    return False


# ============================================================
# تشغيل المحادثة
# ============================================================

def chat_with_agent():

    print("\n--- تم تشغيل AI Agent بنجاح ---")

    print("جاري تحميل العقارات من Google Sheets...")

    properties = get_properties_from_sheet()

    print(
        f"✅ تم تحميل {len(properties)} عقار من Google Sheets."
    )

    print("اكتب exit للخروج.\n")

    previous_interaction_id = None

    while True:

        user_input = input("العميل: ").strip()

        if user_input.lower() == "exit":

            print("تم إغلاق AI Agent.")

            break

        if not user_input:
            continue

        try:

            interaction = send_message(
                user_input,
                properties,
                previous_interaction_id
            )

            data = json.loads(
                interaction.output_text
            )

            print("\nالوكيل:")

            print(
                data["reply"]
            )

            print("\n--- تحليل العميل ---")

            print(
                "الحالة:",
                data["status"]
            )

            print(
                "درجة الاهتمام:",
                data["interest_score"]
            )

            print(
                "بيانات العميل:",
                data["customer_data"]
            )

            print(
                "البيانات الناقصة:",
                data["missing_data"]
            )

            # تسجيل العميل تلقائيًا
            if should_save_lead(data):

                save_result = save_lead_to_sheet(data)

                if save_result.get("success"):

                    print(
                        "✅ تم تسجيل العميل تلقائيًا "
                        "في Google Sheets."
                    )

                else:

                    print(
                        "⚠️ تعذر تسجيل العميل "
                        "في Google Sheets:"
                    )

                    print(
                        save_result
                    )

            previous_interaction_id = (
                interaction.id
            )

            print()

        except Exception as error:

            print("\nحدث خطأ:")

            print(error)

            print()


# ============================================================
# تشغيل البرنامج
# ============================================================

if __name__ == "__main__":
    chat_with_agent()