# ============================================================
# AIM CORE
# المحرك الأساسي لوكيل الذكاء الاصطناعي
# ============================================================

class AIMCore:

    def __init__(self):
        # تخزين بيانات العميل أثناء المحادثة
        self.customer_data = {}

        # حفظ العقارات أو المنتجات أو الخدمات
        # التي تم عرضها للعميل
        self.shown_items = []

        # حفظ سياق المحادثة
        self.conversation_history = []

    # --------------------------------------------------------
    # تحديث بيانات العميل
    # --------------------------------------------------------

    def update_customer_data(self, data):

        if not isinstance(data, dict):
            return

        for key, value in data.items():

            if value is not None and value != "":
                self.customer_data[key] = value

    # --------------------------------------------------------
    # إضافة رسالة للمحادثة
    # --------------------------------------------------------

    def add_message(self, role, message):

        self.conversation_history.append({
            "role": role,
            "message": message
        })

    # --------------------------------------------------------
    # تسجيل العناصر التي تم عرضها
    # --------------------------------------------------------

    def mark_item_as_shown(self, item_id):

        if item_id not in self.shown_items:
            self.shown_items.append(item_id)

    # --------------------------------------------------------
    # معرفة العناصر التي لم يتم عرضها
    # --------------------------------------------------------

    def filter_unshown_items(self, items, id_field="id"):

        result = []

        for item in items:

            item_id = item.get(id_field)

            if item_id not in self.shown_items:
                result.append(item)

        return result