import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
def check_code(width=120, height=30, char_length=5, font_file='Monaco.ttf', font_size=28):
    code = []
    img = Image.new(mode='RGB', size=(width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img, mode='RGB')

    def rndChar():
        """
        生成随机字母
        :return:
        """
        return chr(random.randint(65, 90))

    def rndColor():
        """
        生成随机颜色
        :return:
        """
        return (random.randint(0, 255), random.randint(10, 255), random.randint(64, 255))

    # 写文字
    font = ImageFont.truetype(font_file, font_size)
    for i in range(char_length):
        char = rndChar()
        code.append(char)
        h = random.randint(0, 4)
        draw.text([i * width / char_length, h], char, font=font, fill=rndColor())

    # 写干扰点
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())

    # 写干扰圆圈
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=rndColor())

    # 画干扰线
    for i in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)

        draw.line((x1, y1, x2, y2), fill=rndColor())

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img, ''.join(code)


def sync_primary_contact(customer, overwrite=False):
    """把客户表上的 contact_person/phone 同步到联系人子表的主联系人。

    老系统仍把客户表这两个字段当作唯一联系人来源，若不回写子表，新系统的
    联系人列表就会与客户表脱节。两种调用场景语义不同：

    - overwrite=True：老系统编辑客户资料，用户就是在改「这个人」，
      直接改写主联系人，不新增记录；
    - overwrite=False：发货时填的收货人，可能是一次性联系人（如「前台小王」），
      必须保留原联系人，只新增一条主联系人并把旧的降级。

    两种情况都优先复用同名记录。异常一律吞掉，绝不影响主流程。
    """
    from cono import models

    try:
        name = (customer.contact_person or '').strip()
        phone = (customer.phone or '').strip()
        if not name:
            return
        contacts = models.CustomerContact.objects.filter(customer=customer)
        if overwrite:
            primary = contacts.filter(is_primary=True).first()
            if primary:
                contacts.exclude(pk=primary.pk).update(is_primary=False)
                primary.name = name
                primary.phone = phone
                primary.save(update_fields=['name', 'phone', 'update_time'])
                return
        same_name = contacts.filter(name=name).first()
        if same_name:
            contacts.exclude(pk=same_name.pk).update(is_primary=False)
            same_name.is_primary = True
            same_name.phone = phone
            same_name.save(update_fields=['is_primary', 'phone', 'update_time'])
            return
        contacts.update(is_primary=False)
        models.CustomerContact.objects.create(
            customer=customer, name=name, phone=phone, is_primary=True)
    except Exception:
        pass
