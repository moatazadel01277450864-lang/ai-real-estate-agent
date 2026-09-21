import os
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY غير موجود في ملف .env")

client = genai.Client(api_key=API_KEY)

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbzotzZVjnuSW3JCgckoy2NN0uqTHB7b1ypJj86xOB2QgoE4y7iTYc1e9TqAx-1uZZcs/exec"
def load_products():
    try:
        response = requests.get(
            GOOGLE_SHEETS_URL,
            params={"sheet": "Products"},
            timeout=15
        )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):
            print("⚠️ تعذر تحميل المنتجات:")
            print(result)
            return []

        products = result.get("data", [])

        print(f"✅ تم تحميل {len(products)} منتج من Google Sheets.")

        return products

    except Exception as error:
        print("⚠️ حدث خطأ أثناء تحميل المنتجات:")
        print(error)
        return []
SYSTEM_INSTRUCTION = """
أنت وكيل مبيعات وخدمة عملاء ذكي لمحل صناعة وبيع إكسسوارات هاند ميد.

هدفك:
مساعدة العميل، فهم طلبه، جمع البيانات المطلوبة، وعدم تأكيد أي طلب قبل اكتمال البيانات اللازمة.

========================
قواعد المحادثة
========================

1. تحدث مع العميل باللغة العربية بطريقة طبيعية وودودة.
2. احتفظ بكل المعلومات التي ذكرها العميل في الرسائل السابقة.
3. لا تطلب من العميل معلومة سبق أن ذكرها.
4. لا تخترع أي معلومات عن المنتجات أو الأسعار أو التوافر أو مواعيد التسليم.
5. إذا كانت هناك بيانات ناقصة، اسأل عنها تدريجيًا وبطريقة طبيعية.
6. لا تسأل عن كل البيانات مرة واحدة إذا كان من الممكن جمعها تدريجيًا.
7. لا تقل إن الطلب تم تأكيده إلا إذا كانت البيانات المطلوبة مكتملة وتم التأكيد فعلًا.
8. إذا قال العميل إنه يريد الطلب، تعامل معه كطلب جاد وراجع البيانات الناقصة.
9. إذا لم يكمل العميل البيانات، لا تعتبر الطلب مؤكدًا.
10. إذا طلب العميل التحدث مع موظف بشري، أو كانت المشكلة تحتاج قرارًا بشريًا، قم بتحويل الحالة إلى human_handoff.
11. لا تخبر العميل بتفاصيل التحليل الداخلي أو درجة الاهتمام.

========================
بيانات العميل والطلب
========================

حاول جمع البيانات التالية عند الحاجة:

- name = اسم العميل
- phone = رقم الهاتف
- product_type = نوع الإكسسوار
- design = التصميم أو الشكل المطلوب
- color = اللون
- material = الخامة
- size = المقاس
- quantity = الكمية
- customization = التخصيص أو التصميم الخاص
- budget = الميزانية
- delivery_method = طريقة الاستلام أو التوصيل
- delivery_time = موعد الاستلام أو التوصيل
- address = العنوان

========================
الطلب المكتمل
========================

قبل اعتبار الطلب جاهزًا للتأكيد، تأكد من وجود البيانات الأساسية المناسبة للطلب.

البيانات الأساسية عادةً:
- المنتج
- الكمية
- التفاصيل المطلوبة للمنتج
- اسم العميل
- رقم الهاتف
- طريقة التوصيل أو الاستلام

إذا كان التوصيل مطلوبًا:
- العنوان

إذا كان العميل طلب موعدًا محددًا:
- delivery_time

إذا كانت هناك معلومة ضرورية غير موجودة:
لا تؤكد الطلب، واسأل العميل عنها.

========================
التحويل لموظف بشري
========================

استخدم الحالة:

human_handoff

عندما:
- يطلب العميل التحدث مع موظف.
- يطلب العميل مساعدة بشرية.
- توجد مشكلة لا تستطيع حلها بثقة.
- يحتاج العميل إلى قرار أو استثناء من الموظف.
- يوجد شك أو تعارض في معلومات الطلب.

عند التحويل لموظف:
- لا تدّعي أن موظفًا رد بالفعل إلا إذا النظام أكد ذلك.
- اجعل الرد للعميل واضحًا ومختصرًا بأن طلبه سيتم تحويله للمتابعة البشرية.

========================
حالات العميل
========================

- new = عميل جديد
- interested = مهتم
- qualified = عميل محتمل مؤهل
- customer = عميل تم تأكيد طلبه
- not_interested = غير مهتم
- human_handoff = يحتاج تدخل موظف بشري

========================
درجة الاهتمام
========================

حدد interest_score من 0 إلى 100.

الدرجة تعكس مدى اهتمام العميل بناءً على المحادثة فقط.

لا تخترع معلومات لرفع الدرجة.

========================
مهم جدًا
========================

لا تعتبر قول العميل:
"عايز أطلب"
أو
"تمام هات الأوردر"

بمثابة طلب مكتمل.

يجب أولًا مراجعة البيانات الناقصة.

ولا تعتبر العميل customer إلا عندما تكون بيانات الطلب الأساسية مكتملة ويمكن اعتبار الطلب جاهزًا للتأكيد.

لا تخترع أي معلومة لم يذكرها العميل.
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {
            "type": "string"
        },
        "status": {
            "type": "string",
           "enum": [
    "new",
    "interested",
    "qualified",
    "customer",
    "not_interested",
    "human_handoff"
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
                "product_type": {
                    "type": ["string", "null"]
                },
                "design": {
                    "type": ["string", "null"]
                },
                "color": {
                    "type": ["string", "null"]
                },
                "material": {
                    "type": ["string", "null"]
                },
                "size": {
                    "type": ["string", "null"]
                },
                "quantity": {
                    "type": ["string", "null"]
                },
                "customization": {
                    "type": ["string", "null"]
                },
                "budget": {
                    "type": ["string", "null"]
                },
                "delivery_method": {
                    "type": ["string", "null"]
                },
                "delivery_time": {
                    "type": ["string", "null"]
                },
                "address": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "name",
                "phone",
                "product_type",
                "design",
                "color",
                "material",
                "size",
                "quantity",
                "customization",
                "budget",
                "delivery_method",
                "delivery_time",
                "address"
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

def send_message(message, previous_interaction_id=None):
    request_data = {
        "model": "gemini-3.6-flash",
        "input": message,
        "system_instruction": SYSTEM_INSTRUCTION,
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": RESPONSE_SCHEMA
        }
    }

    if previous_interaction_id:
        request_data["previous_interaction_id"] = previous_interaction_id

    return client.interactions.create(**request_data)

def save_lead_to_sheet(data):
    now = datetime.now()
    customer_data = data.get("customer_data", {})

    payload = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "name": customer_data.get("name") or "",
        "phone": customer_data.get("phone") or "",
        "product_type": customer_data.get("product_type") or "",
        "design": customer_data.get("design") or "",
        "color": customer_data.get("color") or "",
        "material": customer_data.get("material") or "",
        "size": customer_data.get("size") or "",
        "quantity": customer_data.get("quantity") or "",
        "customization": customer_data.get("customization") or "",
        "budget": customer_data.get("budget") or "",
        "delivery_method": customer_data.get("delivery_method") or "",
        "delivery_time": customer_data.get("delivery_time") or "",
        "address": customer_data.get("address") or "",
        "status": data.get("status") or "",
        "interest_score": data.get("interest_score", ""),
        "notes": ""
    }

    response = requests.post(
        GOOGLE_SHEETS_URL,
        json=payload,
        timeout=15
    )

    response.raise_for_status()
    return response.json()

def should_save_lead(data):
    customer_data = data.get("customer_data", {})
    phone = customer_data.get("phone")
    status = data.get("status")

    if status == "human_handoff":
        return False

    if phone:
        return True

    if status == "qualified":
        return True

    return False

CONVERSATION_FILE = "conversation_history.json"


def save_conversation_message(role, message):
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as file:
                history = json.load(file)
        else:
            history = []

        history.append({
            "role": role,
            "message": message,
           "timestamp": datetime.now().isoformat()
        })

        with open(CONVERSATION_FILE, "w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)

    except Exception as error:
        print("⚠️ تعذر حفظ سجل المحادثة:")
        print(error)

products = load_products()

print("\n--- المنتجات المحملة ---")
for product in products:
    print(product)

    
def chat_with_agent():
    print("\n--- تم تشغيل AI Agent لمحل الإكسسوارات ---")
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
            save_conversation_message("customer", user_input)

            interaction = send_message(
                user_input,
                previous_interaction_id
            )

            data = json.loads(interaction.output_text)

            print("\nالوكيل:")
            print(data["reply"])

            save_conversation_message("agent", data["reply"])

            print("\n--- تحليل العميل ---")
            print("الحالة:", data["status"])
            print("درجة الاهتمام:", data["interest_score"])
            print("بيانات العميل:", data["customer_data"])
            print("البيانات الناقصة:", data["missing_data"])

            if should_save_lead(data):
                save_result = save_lead_to_sheet(data)

                if save_result.get("success"):
                    print("✅ تم تسجيل العميل تلقائيًا في Google Sheets.")
                else:
                    print("⚠️ تعذر تسجيل العميل في Google Sheets:")
                    print(save_result)

            previous_interaction_id = interaction.id

            print()

        except Exception as error:
            print("\nحدث خطأ:")
            print(error)
            print()


if __name__ == "__main__":
    chat_with_agent()