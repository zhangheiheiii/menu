import streamlit as st

#基础配置
st.set_page_config(page_title="每日食堂 · 点菜", page_icon="🍽️", layout="wide")

SECRET = "boss"  # 隐藏后台码，可自行修改

#初始化数据（存在 session 中，刷新不丢）
if "menu" not in st.session_state:
    st.session_state.menu = {
        "宫保鸡丁": 18.0,
        "鱼香肉丝": 16.0,
        "番茄炒蛋": 12.0,
        "可乐": 3.0,
        "米饭": 2.0,
    }
if "order" not in st.session_state:
    st.session_state.order = {}

menu = st.session_state.menu      # 菜单：{菜名: 价格}
order = st.session_state.order    # 订单：{菜名: 份数}


#工具函数
def total_price():
    return sum(menu.get(name, 0) * qty for name, qty in order.items())


def add_dish(name, qty):
    if qty > 0:
        order[name] = order.get(name, 0) + qty


def change_qty(name, delta):
    new_qty = order.get(name, 0) + delta
    if new_qty <= 0:
        order.pop(name, None)
    else:
        order[name] = new_qty


def checkout():
    """结账：生成小票并清空订单"""
    lines = [(name, qty, menu.get(name, 0) * qty) for name, qty in order.items()]
    total = sum(line[2] for line in lines)
    st.session_state.receipt = {"lines": lines, "total": total}
    order.clear()


#页面头部
st.title("每日食堂 · 点菜")
mode = st.radio("模式", ["顾客点菜", "后台管理"], horizontal=True, label_visibility="collapsed")
st.divider()

# 最近一次结账小票
receipt = st.session_state.get("receipt")
if receipt:
    st.success("结账成功，欢迎下次光临！")
    st.write("订单详情：")
    for name, qty, sub in receipt["lines"]:
        st.write(f"- {name} × {qty} = ¥{sub:g}")
    st.write(f"总价：¥{receipt['total']:g}")
    st.button("关闭小票", on_click=lambda: st.session_state.update(receipt=None))
    st.divider()

#顾客点菜
if mode == "顾客点菜":
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.subheader("今日菜单")
        if not menu:
            st.info("菜单暂时为空，请到「后台管理」添加菜品")
        for name in list(menu.keys()):
            c1, c2, c3 = st.columns([3, 2, 1.2])
            c1.markdown(f"{name}　¥{menu[name]:g}")
            qty = c2.number_input("份数", min_value=0, max_value=20, value=1, step=1,
                                  key=f"qty_{name}", label_visibility="collapsed")
            c3.button("加入", key=f"add_{name}", use_container_width=True,
                      on_click=add_dish, args=(name, qty))

    with right:
        st.subheader("当前订单")
        if not order:
            st.caption("还没有点菜，去左边点几道吧～")
        else:
            for name in list(order.keys()):
                qty = order[name]
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(name)
                c2.write(f"¥{menu.get(name, 0) * qty:g}")
                c3.button("−", key=f"minus_{name}", on_click=change_qty, args=(name, -1))
                c4.button("＋", key=f"plus_{name}", on_click=change_qty, args=(name, 1))
            st.divider()
            st.markdown(f"### 合计：¥{total_price():g}")
            c1, c2 = st.columns(2)
            c1.button("结账", type="primary", on_click=checkout, use_container_width=True)
            c2.button("清空", on_click=order.clear, use_container_width=True)

#后台管理
else:
    pwd = st.text_input("请输入后台密码", type="password",
                        placeholder="输入后台码后可管理菜单和订单")
    if pwd != SECRET:
        st.info("💡 输入正确的后台码（默认 boss）后即可进入管理界面")
        st.stop()

    st.success("已进入后台管理模式")
    tabs = st.tabs(["修改价格", "新增菜品", "删除菜品", "修改订单"])

    # 1.修改价格
    with tabs[0]:
        if not menu:
            st.info("菜单为空")
        else:
            name = st.selectbox("选择菜品", list(menu.keys()), key="price_name")
            new_price = st.number_input("新价格", min_value=0.0, step=1.0,
                                        value=float(menu[name]), key=f"price_value_{name}")
            if st.button("保存价格", key="price_save"):
                menu[name] = float(new_price)
                st.success(f"已修改：{name} = {new_price:g} 元")

    # 2.新增菜品
    with tabs[1]:
        with st.form("add_form", clear_on_submit=True):
            new_name = st.text_input("新菜名")
            price = st.number_input("价格", min_value=0.0, step=1.0, value=10.0)
            submitted = st.form_submit_button("上架")
        if submitted:
            new_name = new_name.strip()
            if not new_name:
                st.error("菜名不能为空")
            elif new_name in menu:
                st.error("菜单里已经有这道菜了")
            else:
                menu[new_name] = float(price)
                st.success(f"已上架：{new_name} {price:g} 元")

    # 3.删除菜品
    with tabs[2]:
        if not menu:
            st.info("菜单为空")
        else:
            def delete_dish(name):
                menu.pop(name, None)
                order.pop(name, None)
                st.session_state.pop("del_name", None)  # 清掉选中状态避免报错

            name = st.selectbox("要下架的菜", list(menu.keys()), key="del_name")
            st.button("下架该菜", key="del_btn", on_click=delete_dish, args=(name,))

    # 4.修改顾客订单
    with tabs[3]:
        if not order:
            st.caption("当前没有订单")
        else:
            new_qty = {}
            for name in list(order.keys()):
                new_qty[name] = st.number_input(
                    f"{name}（现有 {order[name]} 份，填 0 即删除）",
                    min_value=0, step=1, value=order[name], key=f"admin_qty_{name}")
            if st.button("保存订单修改", key="order_save"):
                for name, q in new_qty.items():
                    if q <= 0:
                        order.pop(name, None)
                    else:
                        order[name] = int(q)
                st.success("订单已修改")
            st.divider()
            st.markdown(f"**合计：¥{total_price():g}**")