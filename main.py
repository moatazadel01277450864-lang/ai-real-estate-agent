import os
import json
import uuid
import threading
import time
import re
from datetime import datetime

import requests
from dotenv import load_dotenv
from openai import OpenAI

from aim_core import AIMCore


# ============================================================
# 1) ENVIRONMENT
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY غير موجود في ملف .env"
    )

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# الموديل الأساسي الحالي
AI_MODEL = "gpt-5.6-luna"

GOOGLE_SHEETS_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzotzZVjnuSW3JCgckoy2NN0uqTHB7b1ypJj86xOB2QgoE4y7iTYc1e9TqAx-1uZZcs/"
    "exec"
)

CONVERSATION_FILE = "conversation_history.json"

PENDING_LEADS_FILE = "pending_leads.json"

PENDING_RETRY_INTERVAL = 60


# ============================================================
# 2) AIM CORE
# ============================================================

aim_core = AIMCore()

print("\n" + "=" * 60)
print("🧠 AI AGENT + AIM CORE")
print("=" * 60)


# ============================================================
# 3) SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
أنت وكيل مبيعات وخدمة عملاء ذكي وقابل للتخصيص لمحل صناعة وبيع إكسسوارات هاند ميد.

أنت جزء من نظام AI Agent يعتمد على AIM Core.

========================
أهدافك الأساسية
========================

1. مساعدة العميل بشكل طبيعي وودود.
2. فهم احتياج العميل.
3. الاحتفاظ بسياق المحادثة.
4. استخدام بيانات المنتجات الموجودة في الكتالوج فقط.
5. جمع بيانات العميل والطلب تدريجيًا.
6. عدم اختراع أي معلومة.
7. عدم اعتبار الطلب مؤكدًا إلا بعد تأكيد العميل صراحة.
8. التعامل مع كل طلب جديد كطلب مستقل.
9. تحويل العميل إلى موظف بشري عند الحاجة.
10. إخراج البيانات بصيغة JSON المحددة في النظام.

========================
قواعد المنتجات
========================

- لا تخترع منتجًا.
- لا تخترع سعرًا.
- لا تخترع لونًا.
- لا تخترع خامة.
- لا تخترع مقاسًا.
- لا تخترع تخصيصًا.
- لا تخترع توافرًا.
- لا تخترع موعد تسليم.
- إذا لم توجد المعلومة في الكتالوج، قل للعميل بوضوح إن المعلومة غير متاحة حاليًا.
- استخدم الكتالوج الحالي فقط.

========================
المحادثة
========================

- تحدث باللغة العربية بطريقة طبيعية وودودة.
- لا تطلب معلومة سبق أن ذكرها العميل.
- اجمع البيانات الناقصة تدريجيًا.
- لا تسأل عن كل البيانات مرة واحدة إذا كان يمكن جمعها بطريقة طبيعية.
- لا تخبر العميل بدرجة اهتمامه.
- لا تخبر العميل بتفاصيل التحليل الداخلي.
- لا تعرض بيانات النظام الداخلية.

========================
بيانات العميل
========================

يمكن جمع:

name
phone

========================
بيانات الطلب
========================

يمكن جمع:

product_type
design
color
material
size
quantity
customization
budget
delivery_method
delivery_time
address

========================
الطلب الجديد
========================

كل طلب منتج جديد يبدأ من الصفر بالنسبة لتفاصيل الطلب.

احتفظ ببيانات العميل الأساسية مثل:
- الاسم
- الهاتف

لكن لا تنقل تلقائيًا تفاصيل طلب قديم إلى طلب جديد.

لا تنقل تلقائيًا:
- المنتج
- اللون
- الخامة
- المقاس
- الكمية
- التخصيص
- الميزانية
- طريقة التوصيل
- موعد التوصيل
- العنوان

إلا إذا أكد العميل أنه يريد استخدامها مرة أخرى.

========================
حالة الطلب Order Status
========================

القيم المسموح بها:

draft
awaiting_confirmation
confirmed
cancelled

draft:
الطلب ما زال يتم تجهيزه أو توجد بيانات ناقصة.

awaiting_confirmation:
كل البيانات الأساسية المطلوبة للطلب مكتملة، وتم عرض ملخص الطلب للعميل، والوكيل ينتظر تأكيد العميل.

confirmed:
العميل أكد الطلب بشكل صريح وواضح.

cancelled:
العميل ألغى الطلب أو طلب إلغاءه.

========================
قواعد تأكيد الطلب
========================

اكتمال البيانات لا يعني تأكيد الطلب.

وجود الاسم والهاتف والعنوان وباقي البيانات لا يعني أن الطلب confirmed.

عندما تكتمل البيانات الأساسية:

1. اعرض ملخص الطلب.
2. وضح المنتج والكمية والاختيارات والإجمالي والبيانات الأساسية.
3. اطلب تأكيدًا صريحًا.

في هذه المرحلة:

order_status = awaiting_confirmation

ولا تستخدم:

order_status = confirmed

إلا بعد تأكيد واضح وصريح من العميل.

أمثلة:

- أيوه أكد الطلب.
- أيوه تمام.
- أكد.
- موافق على الطلب.
- تمام نفذه.
- أيوه اطلبه.

========================
ممنوع التأكيد التلقائي
========================

لا تعتبر هذه العبارات تأكيدًا نهائيًا:

- عايز إسورة.
- عايز أطلب.
- تمام.
- ماشي.
- كويس.
- حلو.
- ابعتلي التفاصيل.
- عايز اللون الذهبي.
- العنوان سموحة.
- رقم موبايلي كذا.

هذه العبارات جزء من المحادثة فقط.

========================
قواعد الإلغاء
========================

إذا قال العميل بوضوح إنه لا يريد الطلب الحالي:

order_status = cancelled

لكن لا تقل "تم إلغاء الطلب" إذا لم يكن هناك طلب فعلي في مرحلة تجهيز.

إذا كان العميل يقول فقط إنه غير مهتم بمنتج قبل إنشاء طلب واضح، يمكن استخدام:

status = not_interested

مع الحفاظ على order_status = draft

ولا تمسح missing_data بدون سبب.

========================
Human Handoff
========================

استخدم:

human_handoff

إذا:

- طلب العميل موظفًا بشريًا.
- طلب المساعدة من شخص.
- توجد مشكلة تحتاج قرارًا بشريًا.
- يوجد استثناء.
- يوجد تعارض أو شك في بيانات الطلب.
- لا تستطيع الإجابة بثقة.

عند التحويل:

- لا تدّعي أن الموظف رد بالفعل.
- أخبر العميل باختصار أن المحادثة سيتم تحويلها للمتابعة البشرية.
- لا تعتبر الحالة Lead جاهزًا للحفظ التلقائي.

========================
الحالات
========================

new
interested
qualified
customer
not_interested
human_handoff

status يصف حالة العميل في رحلة البيع.

order_status يصف حالة الطلب نفسه.

لا تخلط بين الاثنين.

========================
Interest Score
========================

interest_score من 0 إلى 100.

الدرجة تعتمد فقط على المعلومات الموجودة في المحادثة.

لا تخترع معلومات لرفع الدرجة.

استخدم منطقًا ثابتًا قدر الإمكان.

لا تغيّر الدرجة عشوائيًا لنفس الحالة.

========================
Lead Saving
========================

إذا كان الهاتف موجودًا، احتفظ به.

إذا لم يكن الهاتف موجودًا، لا تخترعه.

إذا كانت البيانات ناقصة، أخرجها داخل missing_data.

إذا كان status = human_handoff فلا تعتبر الحالة Lead جاهزًا للحفظ التلقائي.

إذا كان order_status = confirmed، احتفظ بهذه الحالة بوضوح.

========================
مهم جدًا
========================

لا تعتبر الطلب مؤكدًا لمجرد أن العميل أبدى الرغبة.

لا تعتبر الطلب مؤكدًا لمجرد اكتمال البيانات.

يجب أن يوجد تأكيد صريح قبل:

order_status = confirmed
"""


# ============================================================
# 4) RESPONSE SCHEMA
# ============================================================

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

        "order_status": {
            "type": "string",
            "enum": [
                "draft",
                "awaiting_confirmation",
                "confirmed",
                "cancelled"
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
            ],

            "additionalProperties": False
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
        "order_status",
        "interest_score",
        "customer_data",
        "missing_data"
    ],

    "additionalProperties": False
}


# ============================================================
# 5) GOOGLE SHEETS - PRODUCTS
# ============================================================

def load_products():

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:

            print(
                f"📦 محاولة تحميل المنتجات "
                f"({attempt}/{max_attempts})..."
            )

            products_url = GOOGLE_SHEETS_URL + "?sheet=Products"

            response = requests.get(
                products_url,
                timeout=(10, 60),
                allow_redirects=False
            )

            if response.status_code in (
                301,
                302,
                303,
                307,
                308
            ):

                redirect_url = response.headers.get(
                    "Location"
                )

                if not redirect_url:

                    raise requests.exceptions.RequestException(
                        "Google Apps Script أعاد Redirect بدون رابط."
                    )

                print(
                    "🔄 تم اكتشاف Redirect من Google Apps Script."
                )

                response = requests.get(
                    redirect_url,
                    timeout=(10, 60),
                    allow_redirects=True
                )

            response.raise_for_status()

            result = response.json()

            if not isinstance(result, dict):

                print(
                    "⚠️ رد Google Sheets ليس بالشكل المتوقع."
                )

                return []

            if not result.get("success"):

                print(
                    "⚠️ تعذر تحميل المنتجات:"
                )

                print(result)

                return []

            loaded_products = result.get(
                "data",
                []
            )

            if not isinstance(
                loaded_products,
                list
            ):

                print(
                    "⚠️ بيانات المنتجات ليست قائمة صحيحة."
                )

                return []

            print(
                f"✅ تم تحميل "
                f"{len(loaded_products)} منتج "
                f"من Google Sheets."
            )

            return loaded_products

        except requests.exceptions.Timeout as error:

            print(
                "⚠️ انتهت مهلة الاتصال بـ Google Sheets."
            )

            print(error)

        except requests.exceptions.RequestException as error:

            print(
                "⚠️ مشكلة في الاتصال بـ Google Sheets:"
            )

            print(error)

        except ValueError as error:

            print(
                "⚠️ Google Sheets لم يرجع JSON صالح:"
            )

            print(error)

            return []

        except Exception as error:

            print(
                "⚠️ حدث خطأ أثناء تحميل المنتجات:"
            )

            print(error)

        if attempt < max_attempts:

            print(
                "🔄 سيتم إعادة المحاولة..."
            )

            time.sleep(2)

    print(
        f"❌ فشل تحميل المنتجات بعد "
        f"{max_attempts} محاولات."
    )

    return []


products = load_products()


# ============================================================
# 6) PRODUCT CATALOG DISPLAY
# ============================================================

print(
    "\n--- المنتجات المحملة ---"
)

for product in products:

    print(product)


# ============================================================
# 7) PRODUCT CATALOG FOR AI
# ============================================================

def build_products_context():

    if not products:

        return (
            "لا يوجد كتالوج منتجات متاح حاليًا."
        )

    return json.dumps(
        products,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# 8) AI REQUEST
# ============================================================

def send_message(
    message,
    previous_response_id=None,
    extra_context=None
):

    products_text = build_products_context()

    context_text = ""

    if extra_context:

        context_text = f"""

========================
سياق إضافي من AIM Core
========================

{json.dumps(
    extra_context,
    ensure_ascii=False,
    indent=2
)}
"""

    system_instruction = f"""
{SYSTEM_INSTRUCTION}

========================
كتالوج المنتجات الحالي
========================

{products_text}

========================
قواعد الكتالوج
========================

- استخدم بيانات الكتالوج فقط.
- لا تخترع بيانات غير موجودة.
- لا تعرض البيانات الداخلية للنظام.

{context_text}
"""

    request_data = {

        "model": AI_MODEL,

        "input": [
            {
                "role": "user",
                "content": message
            }
        ],

        "instructions": system_instruction,

        "text": {
            "format": {
                "type": "json_schema",
                "name": "ai_agent_response",
                "strict": True,
                "schema": RESPONSE_SCHEMA
            }
        },

        "store": True
    }

    if previous_response_id:

        request_data[
            "previous_response_id"
        ] = previous_response_id

    return client.responses.create(
        **request_data
    )


# ============================================================
# 9) CONVERSATION HISTORY
# ============================================================

def save_conversation_message(
    role,
    message
):

    try:

        history = []

        if os.path.exists(
            CONVERSATION_FILE
        ):

            try:

                with open(
                    CONVERSATION_FILE,
                    "r",
                    encoding="utf-8"
                ) as file:

                    loaded_history = json.load(
                        file
                    )

                    if isinstance(
                        loaded_history,
                        list
                    ):

                        history = loaded_history

            except Exception:

                history = []

        history.append({

            "message_id": str(
                uuid.uuid4()
            ),

            "role": role,

            "message": message,

            "timestamp": datetime.now().isoformat()
        })

        with open(
            CONVERSATION_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                history,
                file,
                ensure_ascii=False,
                indent=2
            )

    except Exception as error:

        print(
            "⚠️ تعذر حفظ سجل المحادثة:"
        )

        print(error)


# ============================================================
# 10) ORDER HELPERS
# ============================================================

VALID_ORDER_STATUSES = {
    "draft",
    "awaiting_confirmation",
    "confirmed",
    "cancelled"
}

ORDER_FIELDS = {
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
}

CUSTOMER_FIELDS = {
    "name",
    "phone"
}


def normalize_text(text):

    if not text:

        return ""

    text = str(text).strip().lower()

    replacements = {

        "أ": "ا",
        "إ": "ا",
        "آ": "ا",

        "ى": "ي",

        "ة": "ه"
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


def is_explicit_confirmation(message):

    normalized = normalize_text(
        message
    )

    confirmation_patterns = [

        r"^ايوه$",
        r"^اه$",
        r"^نعم$",
        r"^اكد$",
        r"^اكد الطلب$",
        r"^موافق$",
        r"^موافق على الطلب$",
        r"^تمام نفذه$",
        r"^ايوه اكد الطلب$",
        r"^ايوه تمام$",
        r"^تمام اطلبه$",
        r"^نفذه$",
        r"^اطلبه$"
    ]

    return any(
        re.match(
            pattern,
            normalized
        )
        for pattern in confirmation_patterns
    )


def is_explicit_cancellation(message):

    normalized = normalize_text(
        message
    )

    cancellation_patterns = [

        r"^الغيه$",
        r"^الغى الطلب$",
        r"^الغيه الطلب$",
        r"^مش عايزه$",
        r"^مش عايز الطلب$",
        r"^مش عايزة الطلب$",
        r"^لا مش عايز$",
        r"^لا مش عايزة$",
        r"^لا الغيه$",
        r"^لا الغيه الطلب$"
    ]

    return any(
        re.match(
            pattern,
            normalized
        )
        for pattern in cancellation_patterns
    )


def normalize_order_status(
    data,
    user_message,
    current_order_status
):

    returned_status = data.get(
        "order_status"
    )

    if current_order_status not in VALID_ORDER_STATUSES:

        current_order_status = "draft"

    # ----------------------------------------
    # Explicit cancellation
    # ----------------------------------------

    if is_explicit_cancellation(
        user_message
    ):

        if current_order_status == "awaiting_confirmation":

            data["order_status"] = "cancelled"

        elif current_order_status == "draft":

            data["order_status"] = "draft"

        else:

            data["order_status"] = current_order_status

        return data

    # ----------------------------------------
    # Explicit confirmation
    # ----------------------------------------

    if is_explicit_confirmation(
        user_message
    ):

        if current_order_status == "awaiting_confirmation":

            data["order_status"] = "confirmed"

            return data

        data["order_status"] = current_order_status

        return data

    # ----------------------------------------
    # AI cannot confirm by itself
    # ----------------------------------------

    if returned_status == "confirmed":

        if current_order_status == "awaiting_confirmation":

            data["order_status"] = "awaiting_confirmation"

        else:

            data["order_status"] = current_order_status

    # ----------------------------------------
    # Prevent invalid state
    # ----------------------------------------

    if data.get(
        "order_status"
    ) not in VALID_ORDER_STATUSES:

        data["order_status"] = (
            current_order_status
        )

    # ----------------------------------------
    # Prevent accidental rollback
    # ----------------------------------------

    if current_order_status == "confirmed":

        data["order_status"] = "confirmed"

    if current_order_status == "cancelled":

        data["order_status"] = "cancelled"

    return data


def build_order_data(data):

    customer_data = data.get(
        "customer_data",
        {}
    )

    order_data = {}

    for field in ORDER_FIELDS:

        value = customer_data.get(
            field
        )

        if value not in ("", None):

            order_data[field] = value

    return order_data


def build_customer_data(data):

    customer_data = data.get(
        "customer_data",
        {}
    )

    cleaned = {}

    for field in CUSTOMER_FIELDS:

        value = customer_data.get(
            field
        )

        if value not in ("", None):

            cleaned[field] = value

    return cleaned


# ============================================================
# 11) LEAD DECISION
# ============================================================

def should_save_lead(data):

    customer_data = data.get(
        "customer_data",
        {}
    )

    phone = customer_data.get(
        "phone"
    )

    status = data.get(
        "status"
    )

    if status == "human_handoff":

        return False

    if phone:

        return True

    return False


# ============================================================
# 11.1) LEAD SIGNATURE
# ============================================================

last_saved_lead_signature = None


def build_lead_signature(data):

    customer_data = data.get(
        "customer_data",
        {}
    )

    relevant_data = {

        "name": customer_data.get(
            "name"
        ),

        "phone": customer_data.get(
            "phone"
        ),

        "product_type": customer_data.get(
            "product_type"
        ),

        "design": customer_data.get(
            "design"
        ),

        "color": customer_data.get(
            "color"
        ),

        "material": customer_data.get(
            "material"
        ),

        "size": customer_data.get(
            "size"
        ),

        "quantity": customer_data.get(
            "quantity"
        ),

        "customization": customer_data.get(
            "customization"
        ),

        "budget": customer_data.get(
            "budget"
        ),

        "delivery_method": customer_data.get(
            "delivery_method"
        ),

        "delivery_time": customer_data.get(
            "delivery_time"
        ),

        "address": customer_data.get(
            "address"
        ),

        "status": data.get(
            "status"
        ),

        "order_status": data.get(
            "order_status"
        ),

        "interest_score": data.get(
            "interest_score"
        )
    }

    return json.dumps(
        relevant_data,
        ensure_ascii=False,
        sort_keys=True
    )


# ============================================================
# 12) GOOGLE SHEETS - SAVE / UPDATE LEAD
# ============================================================

def save_lead_to_sheet(data):

    now = datetime.now()

    customer_data = data.get(
        "customer_data",
        {}
    )

    payload = {

        "date": now.strftime(
            "%Y-%m-%d"
        ),

        "time": now.strftime(
            "%H:%M:%S"
        ),

        "name": customer_data.get(
            "name"
        ) or "",

        "phone": customer_data.get(
            "phone"
        ) or "",

        "product_type": customer_data.get(
            "product_type"
        ) or "",

        "design": customer_data.get(
            "design"
        ) or "",

        "color": customer_data.get(
            "color"
        ) or "",

        "material": customer_data.get(
            "material"
        ) or "",

        "size": customer_data.get(
            "size"
        ) or "",

        "quantity": customer_data.get(
            "quantity"
        ) or "",

        "customization": customer_data.get(
            "customization"
        ) or "",

        "budget": customer_data.get(
            "budget"
        ) or "",

        "delivery_method": customer_data.get(
            "delivery_method"
        ) or "",

        "delivery_time": customer_data.get(
            "delivery_time"
        ) or "",

        "address": customer_data.get(
            "address"
        ) or "",

        "status": data.get(
            "status"
        ) or "",

        "order_status": data.get(
            "order_status"
        ) or "draft",

        "interest_score": data.get(
            "interest_score",
            ""
        ),

        "notes": ""
    }

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1
    ):

        response = None

        try:

            print(
                f"📤 محاولة حفظ العميل في Google Sheets "
                f"({attempt}/{max_attempts})..."
            )

            response = requests.post(
                GOOGLE_SHEETS_URL,
                json=payload,
                timeout=(10, 60)
            )

            print(
                f"📡 Google Sheets HTTP Status: "
                f"{response.status_code}"
            )

            response.raise_for_status()

            result = response.json()

            if (
                isinstance(
                    result,
                    dict
                )
                and result.get(
                    "success"
                ) is False
            ):

                raise Exception(
                    f"Google Sheets رفض العملية: {result}"
                )

            print(
                "✅ تم تسجيل/تحديث العميل تلقائيًا "
                "في Google Sheets."
            )

            return result

        except requests.exceptions.Timeout as error:

            print(
                "⚠️ انتهت مهلة الاتصال بـ Google Sheets."
            )

            print(
                f"التفاصيل: {error}"
            )

        except requests.exceptions.HTTPError as error:

            status_code = (
                response.status_code
                if response is not None
                else "غير معروف"
            )

            print(
                f"⚠️ Google Sheets رجع HTTP Error "
                f"{status_code}."
            )

            print(
                f"التفاصيل: {error}"
            )

        except requests.exceptions.RequestException as error:

            print(
                "⚠️ حدث خطأ في الاتصال بـ Google Sheets."
            )

            print(
                f"التفاصيل: {error}"
            )

        except ValueError as error:

            print(
                "⚠️ Google Sheets رد برد غير صالح "
                "(ليس JSON صحيحًا)."
            )

            print(
                f"التفاصيل: {error}"
            )

        except Exception as error:

            print(
                "⚠️ حدث خطأ غير متوقع أثناء حفظ العميل:"
            )

            print(error)

        if attempt < max_attempts:

            print(
                "🔄 سيتم إعادة المحاولة..."
            )

            time.sleep(2)

    print(
        "❌ فشل حفظ العميل بعد جميع المحاولات."
    )

    return None


# ============================================================
# 12.1) PENDING LEADS - LOCAL BACKUP
# ============================================================

def save_pending_lead(data):

    try:

        pending_leads = []

        if os.path.exists(
            PENDING_LEADS_FILE
        ):

            try:

                with open(
                    PENDING_LEADS_FILE,
                    "r",
                    encoding="utf-8"
                ) as file:

                    pending_leads = json.load(
                        file
                    )

                if not isinstance(
                    pending_leads,
                    list
                ):

                    pending_leads = []

            except Exception:

                pending_leads = []

        customer_data = data.get(
            "customer_data",
            {}
        )

        phone = customer_data.get(
            "phone"
        )

        for item in pending_leads:

            old_data = item.get(
                "data",
                {}
            )

            old_customer_data = old_data.get(
                "customer_data",
                {}
            )

            old_phone = old_customer_data.get(
                "phone"
            )

            if (
                phone
                and old_phone
                and phone == old_phone
            ):

                item["data"] = data

                item["updated_at"] = (
                    datetime.now().isoformat()
                )

                with open(
                    PENDING_LEADS_FILE,
                    "w",
                    encoding="utf-8"
                ) as file:

                    json.dump(
                        pending_leads,
                        file,
                        ensure_ascii=False,
                        indent=2
                    )

                print(
                    "💾 تم تحديث الـLead الموجود "
                    "في قائمة الانتظار."
                )

                return True

        pending_leads.append({

            "saved_at": datetime.now().isoformat(),

            "data": data
        })

        with open(
            PENDING_LEADS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                pending_leads,
                file,
                ensure_ascii=False,
                indent=2
            )

        print(
            f"💾 تم حفظ الـLead مؤقتًا محليًا "
            f"في {PENDING_LEADS_FILE}"
        )

        return True

    except Exception as error:

        print(
            "❌ فشل حفظ الـLead محليًا:"
        )

        print(error)

        return False


# ============================================================
# 12.2) LEAD SAVE HANDLER
# ============================================================

def handle_lead_save(data):

    global last_saved_lead_signature

    if not should_save_lead(
        data
    ):

        return False

    current_signature = build_lead_signature(
        data
    )

    if (
        last_saved_lead_signature
        == current_signature
    ):

        print(
            "ℹ️ تم تجاهل حفظ مكرر لنفس بيانات الـLead."
        )

        return True

    try:

        save_result = save_lead_to_sheet(
            data
        )

        if save_result is not None:

            last_saved_lead_signature = (
                current_signature
            )

            print(
                "✅ تم حفظ الـLead بنجاح."
            )

            return True

        print(
            "⚠️ تعذر حفظ الـLead في Google Sheets."
        )

        print(
            "💾 سيتم حفظه محليًا مؤقتًا."
        )

        save_pending_lead(
            data
        )

        return False

    except Exception as error:

        print(
            "⚠️ حدث خطأ أثناء حفظ الـLead:"
        )

        print(error)

        print(
            "💾 سيتم حفظ الـLead محليًا."
        )

        save_pending_lead(
            data
        )

        return False


# ============================================================
# 12.3) RETRY PENDING LEADS
# ============================================================

def retry_pending_leads():

    if not os.path.exists(
        PENDING_LEADS_FILE
    ):

        return

    try:

        with open(
            PENDING_LEADS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            pending_leads = json.load(
                file
            )

        if not isinstance(
            pending_leads,
            list
        ):

            print(
                "⚠️ ملف pending_leads.json غير صالح."
            )

            return

        if not pending_leads:

            return

        print(
            f"\n🔄 إعادة محاولة رفع "
            f"{len(pending_leads)} Lead معلق..."
        )

        remaining_leads = []

        for index, item in enumerate(
            pending_leads,
            start=1
        ):

            data = item.get(
                "data"
            )

            if not data:

                continue

            if not should_save_lead(data):

                continue

            print(
                f"📤 Lead {index}/"
                f"{len(pending_leads)}..."
            )

            try:

                result = save_lead_to_sheet(
                    data
                )

                if result is not None:

                    print(
                        "✅ تم رفع الـLead بنجاح."
                    )

                else:

                    print(
                        "⚠️ لم يتم رفع الـLead."
                    )

                    remaining_leads.append(
                        item
                    )

            except Exception as error:

                print(
                    "⚠️ خطأ أثناء إعادة رفع الـLead:"
                )

                print(error)

                remaining_leads.append(
                    item
                )

        with open(
            PENDING_LEADS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                remaining_leads,
                file,
                ensure_ascii=False,
                indent=2
            )

        if remaining_leads:

            print(
                f"📦 ما زال هناك "
                f"{len(remaining_leads)} Lead "
                "معلق."
            )

        else:

            print(
                "🎉 تم رفع جميع الـLeads المعلقة بنجاح."
            )

    except Exception as error:

        print(
            "❌ فشل معالجة الـPending Leads:"
        )

        print(error)


# ============================================================
# 12.4) BACKGROUND RETRY WORKER
# ============================================================

def pending_leads_worker():

    print(
        "🔄 Background Retry Worker بدأ العمل."
    )

    while True:

        try:

            retry_pending_leads()

        except Exception as error:

            print(
                "⚠️ خطأ في Background Retry Worker:"
            )

            print(error)

        time.sleep(
            PENDING_RETRY_INTERVAL
        )


def start_pending_leads_worker():

    worker = threading.Thread(
        target=pending_leads_worker,
        daemon=True,
        name="PendingLeadsWorker"
    )

    worker.start()

    print(
        "✅ تم تشغيل نظام الاسترداد التلقائي للـLeads."
    )


# ============================================================
# 13) AIM CORE SAFE HELPERS
# ============================================================

def update_core_customer(data):

    customer_data = build_customer_data(
        data
    )

    if not customer_data:

        return

    try:

        method = getattr(
            aim_core,
            "update_customer_data",
            None
        )

        if callable(method):

            method(
                customer_data
            )

            print(
                "✅ تم تحديث بيانات العميل في AIM Core."
            )

    except Exception as error:

        print(
            "⚠️ تعذر تحديث AIM Core customer:"
        )

        print(error)


def add_core_message(
    role,
    message
):

    try:

        method = getattr(
            aim_core,
            "add_message",
            None
        )

        if callable(method):

            method(
                role,
                message
            )

    except Exception as error:

        print(
            "⚠️ تعذر إضافة الرسالة إلى AIM Core:"
        )

        print(error)


def find_latest_core_order_id():
    """
    العثور على آخر Order نشط للعميل الحالي فقط.

    الطلب النشط:
    - draft
    - awaiting_confirmation

    الطلبات النهائية لا يتم استرجاعها كطلب نشط:
    - confirmed
    - cancelled

    الهدف:
    منع محادثة جديدة من تعديل طلب قديم تم تأكيده أو إلغاؤه.
    """

    try:

        order_manager = getattr(
            aim_core,
            "order_manager",
            None
        )

        if order_manager is None:
            return None

        orders = getattr(
            order_manager,
            "orders",
            None
        )

        if not orders:
            return None

        if isinstance(
            orders,
            dict
        ):
            order_values = list(
                orders.values()
            )

        elif isinstance(
            orders,
            list
        ):
            order_values = orders

        else:
            return None

        customer_id = getattr(
            aim_core,
            "customer_id",
            None
        )

        # نحتفظ فقط بالطلبات النشطة.
        active_orders = []

        for order in order_values:

            if isinstance(
                order,
                dict
            ):

                order_customer_id = (
                    order.get("customer_id")
                )

                order_id = (
                    order.get("order_id")
                    or order.get("id")
                )

                # AIM Core يخزن الحالة الأساسية في status،
                # لكن بعض الطلبات القديمة تم حفظ حالتها داخل data فقط.
                status = order.get("status")

                order_data = order.get("data")

                if (
                    status == "draft"
                    and isinstance(order_data, dict)
                    and order_data.get("status")
                ):
                    status = order_data.get("status")

                if not status:
                    status = order.get("order_status")

            else:

                order_customer_id = getattr(
                    order,
                    "customer_id",
                    None
                )

                order_id = (
                    getattr(
                        order,
                        "order_id",
                        None
                    )
                    or getattr(
                        order,
                        "id",
                        None
                    )
                )

                # نفس الـFallback للطلبات القديمة:
                # لو status الأساسي ما زال draft، نقرأ data.status.
                status = getattr(
                    order,
                    "status",
                    None
                )

                order_data = getattr(
                    order,
                    "data",
                    None
                )

                if (
                    status == "draft"
                    and isinstance(order_data, dict)
                    and order_data.get("status")
                ):
                    status = order_data.get("status")

                if not status:
                    status = getattr(
                        order,
                        "order_status",
                        None
                    )

            if not order_id:
                continue

            if (
                customer_id
                and order_customer_id
                and order_customer_id != customer_id
            ):
                continue

            # فقط الطلبات غير النهائية تعتبر نشطة.
            if status in (
                "draft",
                "awaiting_confirmation"
            ):
                active_orders.append(order)

        if not active_orders:
            return None

        # آخر طلب نشط.
        latest_order = active_orders[-1]

        if isinstance(
            latest_order,
            dict
        ):

            return (
                latest_order.get("order_id")
                or latest_order.get("id")
            )

        return (
            getattr(
                latest_order,
                "order_id",
                None
            )
            or getattr(
                latest_order,
                "id",
                None
            )
        )

    except Exception as error:

        print(
            "⚠️ تعذر تحديد آخر Order نشط من AIM Core:"
        )

        print(error)

        return None


def build_core_context():

    context = {}

    try:

        context["customer_data"] = dict(
            getattr(
                aim_core,
                "customer_data",
                {}
            )
        )

    except Exception:

        context["customer_data"] = {}

    try:

        context["conversation_messages"] = len(
            getattr(
                aim_core,
                "conversation_history",
                []
            )
        )

    except Exception:

        context["conversation_messages"] = 0

    try:

        context["active_core_order_id"] = (
            core_order_id
        )

    except Exception:

        context["active_core_order_id"] = None

    return context


# ============================================================
# 13.1) AIM CORE ORDER SYNC
# ============================================================

core_order_id = find_latest_core_order_id()


def sync_core_order(
    data,
    previous_order_status
):

    global core_order_id

    try:

        order_status = data.get(
            "order_status",
            "draft"
        )

        if order_status not in VALID_ORDER_STATUSES:

            order_status = "draft"

        order_data = build_order_data(
            data
        )

        # ----------------------------------------------------
        # لا ننشئ Order فارغًا
        # ----------------------------------------------------

        has_order_data = bool(
            order_data
        )

        if (
            not has_order_data
            and order_status == "draft"
        ):

            return

        # ----------------------------------------------------
        # منع التعديل على طلب مؤكد أو ملغى
        # ----------------------------------------------------

        if previous_order_status == "confirmed":

            order_status = "confirmed"

        if previous_order_status == "cancelled":

            order_status = "cancelled"

        # ----------------------------------------------------
        # إنشاء Order جديد
        # ----------------------------------------------------

        if not core_order_id:

            create_method = getattr(
                aim_core,
                "create_order",
                None
            )

            if not callable(create_method):

                print(
                    "⚠️ AIM Core لا يحتوي على create_order."
                )

                return

            order_payload = dict(
                order_data
            )

            order_payload[
                "order_status"
            ] = order_status

            created_order = create_method(
                order_payload
            )

            created_id = None

            if isinstance(
                created_order,
                dict
            ):

                created_id = (
                    created_order.get("order_id")
                    or created_order.get("id")
                )

            else:

                created_id = (
                    getattr(
                        created_order,
                        "order_id",
                        None
                    )
                    or getattr(
                        created_order,
                        "id",
                        None
                    )
                )

            if created_id:

                core_order_id = created_id

                print(
                    f"✅ تم إنشاء Order في AIM Core: "
                    f"{core_order_id}"
                )

            else:

                print(
                    "⚠️ تم إنشاء Order لكن لم يتم العثور على ID."
                )

            return

        # ----------------------------------------------------
        # تحديث Order موجود
        # ----------------------------------------------------

        update_method = getattr(
            aim_core,
            "update_order",
            None
        )

        if not callable(update_method):

            print(
                "⚠️ AIM Core لا يحتوي على update_order."
            )

            return

        # AIM Core الرسمي يستخدم حالات مختلفة عن واجهة الوكيل.
        # awaiting_confirmation في main.py تقابل pending في AIM Core.
        core_status_map = {
            "draft": "draft",
            "awaiting_confirmation": "pending",
            "confirmed": "confirmed",
            "cancelled": "cancelled"
        }

        core_status = core_status_map.get(
            order_status,
            "draft"
        )

        updated_order = None

        # أولًا: تحديث بيانات الطلب.
        # لا نعتمد على update_order لتغيير status الأساسي،
        # لأنه يحدّث order.data فقط.
        updated_order = update_method(
            core_order_id,
            {
                "data": order_data,
                "status": order_status
            },
            "ai_agent"
        )

        # ثانيًا: تحديث status الأساسي عبر set_status في AIM Core.
        order_manager = getattr(
            aim_core,
            "order_manager",
            None
        )

        set_status_method = getattr(
            order_manager,
            "set_status",
            None
        ) if order_manager is not None else None

        if callable(set_status_method):

            set_status_method(
                aim_core.business_id,
                core_order_id,
                core_status
            )

        else:

            print(
                "⚠️ AIM Core لا يحتوي على set_status؛ "
                "تم تحديث بيانات الطلب فقط."
            )

        print(
            f"✅ تم تحديث Order في AIM Core: "
            f"{core_order_id} | "
            f"status={core_status}"
        )

        return updated_order

    except TypeError as error:

        print(
            "⚠️ تعذر تحديث Order بسبب اختلاف توقيع الدالة:"
        )

        print(error)

    except Exception as error:

        print(
            "⚠️ تعذر مزامنة Order مع AIM Core:"
        )

        print(error)


# ============================================================
# 13.2) AIM CORE LEAD SYNC
# ============================================================

def sync_core_lead(data):

    try:

        if not should_save_lead(
            data
        ):

            return False

        create_lead_method = getattr(
            aim_core,
            "create_or_update_lead",
            None
        )

        if not callable(
            create_lead_method
        ):

            print(
                "⚠️ AIM Core لا يحتوي على create_or_update_lead."
            )

            return False

        customer_data = data.get(
            "customer_data",
            {}
        )

        lead_data = {

            "name": customer_data.get(
                "name"
            ),

            "phone": customer_data.get(
                "phone"
            ),

            "product_type": customer_data.get(
                "product_type"
            ),

            "design": customer_data.get(
                "design"
            ),

            "color": customer_data.get(
                "color"
            ),

            "material": customer_data.get(
                "material"
            ),

            "size": customer_data.get(
                "size"
            ),

            "quantity": customer_data.get(
                "quantity"
            ),

            "customization": customer_data.get(
                "customization"
            ),

            "budget": customer_data.get(
                "budget"
            ),

            "delivery_method": customer_data.get(
                "delivery_method"
            ),

            "delivery_time": customer_data.get(
                "delivery_time"
            ),

            "address": customer_data.get(
                "address"
            ),

            "order_status": data.get(
                "order_status",
                "draft"
            )
        }

        result = create_lead_method(
            data.get(
                "status",
                "new"
            ),
            data.get(
                "interest_score",
                0
            ),
            lead_data
        )

        print(
            "✅ تم مزامنة الـLead مع AIM Core."
        )

        return result

    except Exception as error:

        print(
            "⚠️ تعذر مزامنة الـLead مع AIM Core:"
        )

        print(error)

        return False


# ============================================================
# 14) HUMAN HANDOFF
# ============================================================

def handle_human_handoff():

    try:

        method = getattr(
            aim_core,
            "request_human_handoff",
            None
        )

        if not callable(method):

            method = getattr(
                aim_core,
                "human_handoff",
                None
            )

        if callable(method):

            result = method()

            print(
                "🔄 Human Handoff:",
                result
            )

    except Exception as error:

        print(
            "⚠️ تعذر تسجيل Human Handoff في AIM Core:"
        )

        print(error)


# ============================================================
# 15) MEDIA FOUNDATION
# ============================================================

def register_media(
    media_type,
    url,
    mime_type="",
    file_name=""
):

    try:

        media_manager = getattr(
            aim_core,
            "media_manager",
            None
        )

        if media_manager is None:

            media_manager = getattr(
                aim_core,
                "media",
                None
            )

        if media_manager is None:

            return None

        create_method = getattr(
            media_manager,
            "create_media",
            None
        )

        if not callable(create_method):

            create_method = getattr(
                media_manager,
                "create",
                None
            )

        if not callable(create_method):

            return None

        return create_method(
            business_id=getattr(
                aim_core.business,
                "business_id",
                None
            ),
            media_type=media_type,
            url=url,
            mime_type=mime_type,
            file_name=file_name
        )

    except TypeError:

        try:

            return create_method(
                media_type=media_type,
                url=url,
                mime_type=mime_type,
                file_name=file_name
            )

        except Exception as error:

            print(
                "⚠️ تعذر تسجيل Media Object:"
            )

            print(error)

            return None

    except Exception as error:

        print(
            "⚠️ تعذر تسجيل Media Object:"
        )

        print(error)

        return None


# ============================================================
# 16) CHAT SESSION
# ============================================================

def chat_with_agent():

    global core_order_id

    print(
        "\n--- تم تشغيل AI Agent لمحل الإكسسوارات ---"
    )

    print(
        f"الموديل: {AI_MODEL}"
    )

    print(
        "اكتب exit للخروج.\n"
    )

    previous_response_id = None

    current_order_status = "draft"

    # --------------------------------------------------------
    # محاولة استرجاع آخر Order من AIM Core
    # --------------------------------------------------------

    if not core_order_id:

        core_order_id = find_latest_core_order_id()

    if core_order_id:

        print(
            f"🔗 تم العثور على Order موجود في AIM Core: "
            f"{core_order_id}"
        )

    while True:

        user_input = input(
            "العميل: "
        ).strip()

        if user_input.lower() == "exit":

            print(
                "تم إغلاق AI Agent."
            )

            break

        if not user_input:

            continue

        previous_order_status = (
            current_order_status
        )

        try:

            # ----------------------------------------
            # Customer message
            # ----------------------------------------

            save_conversation_message(
                "customer",
                user_input
            )

            add_core_message(
                "customer",
                user_input
            )

            # ----------------------------------------
            # AIM Core context
            # ----------------------------------------

            core_context = build_core_context()

            core_context["order_status"] = (
                current_order_status
            )

            # ----------------------------------------
            # AI request
            # ----------------------------------------

            interaction = send_message(
                user_input,
                previous_response_id,
                core_context
            )

            # ----------------------------------------
            # Parse JSON
            # ----------------------------------------

            output_text = getattr(
                interaction,
                "output_text",
                None
            )

            if not output_text:

                raise ValueError(
                    "AI لم يرجع output_text."
                )

            data = json.loads(
                output_text
            )

            if not isinstance(
                data,
                dict
            ):

                raise ValueError(
                    "استجابة AI ليست Object صالح."
                )

            # ----------------------------------------
            # Normalize order status
            # ----------------------------------------

            data = normalize_order_status(
                data,
                user_input,
                current_order_status
            )

            # ----------------------------------------
            # Agent reply
            # ----------------------------------------

            reply = data.get(
                "reply",
                ""
            )

            if not isinstance(
                reply,
                str
            ):

                reply = str(reply)

            print(
                "\nالوكيل:"
            )

            print(
                reply
            )

            # ----------------------------------------
            # Save agent message
            # ----------------------------------------

            save_conversation_message(
                "agent",
                reply
            )

            add_core_message(
                "agent",
                reply
            )

            # ----------------------------------------
            # Update customer
            # ----------------------------------------

            update_core_customer(
                data
            )

            # ----------------------------------------
            # Update order status
            # ----------------------------------------

            current_order_status = data.get(
                "order_status",
                current_order_status
            )

            if current_order_status not in VALID_ORDER_STATUSES:

                current_order_status = (
                    previous_order_status
                )

            # ----------------------------------------
            # Sync order with AIM Core
            # ----------------------------------------

            sync_core_order(
                data,
                previous_order_status
            )

            # ----------------------------------------
            # Analysis
            # ----------------------------------------

            print(
                "\n--- تحليل العميل ---"
            )

            print(
                "الحالة:",
                data.get(
                    "status"
                )
            )

            print(
                "حالة الطلب:",
                current_order_status
            )

            print(
                "درجة الاهتمام:",
                data.get(
                    "interest_score"
                )
            )

            print(
                "بيانات العميل:",
                data.get(
                    "customer_data"
                )
            )

            print(
                "البيانات الناقصة:",
                data.get(
                    "missing_data"
                )
            )

            # ----------------------------------------
            # Human Handoff
            # ----------------------------------------

            if data.get(
                "status"
            ) == "human_handoff":

                handle_human_handoff()

                print(
                    "🔄 تم تحويل الحالة للمتابعة البشرية."
                )

            # ----------------------------------------
            # Lead Save - Google Sheets
            # ----------------------------------------

            handle_lead_save(
                data
            )

            # ----------------------------------------
            # Lead Sync - AIM Core
            # ----------------------------------------

            sync_core_lead(
                data
            )

            # ----------------------------------------
            # Final order state
            # ----------------------------------------

            if current_order_status == "confirmed":

                print(
                    "✅ الطلب مؤكد رسميًا."
                )

            elif current_order_status == "cancelled":

                print(
                    "❌ تم إلغاء الطلب."
                )

            elif current_order_status == "awaiting_confirmation":

                print(
                    "⏳ الطلب في انتظار تأكيد العميل."
                )

            # ----------------------------------------
            # Continue AI response chain
            # ----------------------------------------

            response_id = getattr(
                interaction,
                "id",
                None
            )

            if response_id:

                previous_response_id = (
                    response_id
                )

            print()

        except json.JSONDecodeError as error:

            print(
                "\n⚠️ AI لم يرجع JSON صالح:"
            )

            print(error)

            print()

        except Exception as error:

            print(
                "\n❌ حدث خطأ:"
            )

            print(error)

            print()


# ============================================================
# 17) LOCAL CORE STATUS
# ============================================================

def local_core_status():

    print(
        "\n--- AIM Core Status ---"
    )

    try:

        print(
            "Business:",
            getattr(
                aim_core,
                "business",
                "متاح"
            )
        )

    except Exception:

        pass

    try:

        print(
            "Customer Data:",
            getattr(
                aim_core,
                "customer_data",
                {}
            )
        )

    except Exception:

        pass

    try:

        print(
            "Conversation Messages:",
            len(
                getattr(
                    aim_core,
                    "conversation_history",
                    []
                )
            )
        )

    except Exception:

        pass

    try:

        print(
            "Current Core Order ID:",
            core_order_id
        )

    except Exception:

        pass


# ============================================================
# 18) STARTUP
# ============================================================

if __name__ == "__main__":

    print(
        "\n" + "=" * 60
    )

    print(
        "🧠 AI AGENT + AIM CORE"
    )

    print(
        "=" * 60
    )

    print(
        "\n--- AI Agent جاهز ---"
    )

    print(
        f"GPT-5.6 Luna: ✅ ({AI_MODEL})"
    )

    print(
        "Google Sheets: ✅"
    )

    print(
        "Product Catalog: ✅"
    )

    print(
        "AIM Core: ✅"
    )

    if core_order_id:

        print(
            f"Active Core Order: ✅ ({core_order_id})"
        )

    else:

        print(
            "Active Core Order: لا يوجد حاليًا"
        )

    # ----------------------------------------
    # Start automatic pending lead recovery
    # ----------------------------------------

    start_pending_leads_worker()

    print(
        "\n--- بدء المحادثة ---"
    )

    print(
        "اكتب رسالة العميل، أو اكتب exit للخروج.\n"
    )

    chat_with_agent()