import os
import shutil
from pywasm import compile
from app.models import User
from app import db

K = 32

def save_uploaded_file(file, user_name):
    user_folder = os.path.join("user_files", f"{user_name}")
    if os.path.exists(user_folder):
        shutil.rmtree(user_folder)
    os.makedirs(user_folder, exist_ok=True)
    file.save(os.path.join(user_folder, "module.py"))

def start_battle(user_id):
    module_pyr = f"user_files.{User.query.get(user_id).username}.module"
    user_id_com = select_random_opponent(user_id)
    module_com = f"user_files.{User.query.get(user_id_com).username}.module"
    logic_code = generate_logic(module_pyr, module_com)
    wasm_code = 0 # todo!

    from game.engine import run_battle
    pyr_wins = run_battle(module_pyr, module_com)
    update_user_rating(user_id, user_id_com, pyr_wins)
    return pyr_wins

def generate_logic(module_pyr, module_com):
    with open("logic_template.py", "r") as template_file:
        template_code = template_file.read()
    logic_code = template_code.replace("PLAYER_MODULE", module_pyr)
    logic_code = logic_code.replace("OPPONENT_MODULE", module_com)
    return logic_code

def select_random_opponent(exclude_user_id):
    import random
    user_ids = [u.id for u in User.query.all() if u.id != exclude_user_id]
    return random.choice(user_ids)

def update_user_rating(pyr_id, com_id, pyr_wins):
    player = User.query.get(pyr_id)
    computer = User.query.get(com_id)
    ra, rb = player.rating, computer.rating
    wab = 1 / (10**((rb - ra) / 400) + 1)
    wba = 1 - wab
    if pyr_wins is None:
        pass
    elif pyr_wins:
        player.rating += K * wba
        computer.rating -= K * wba
    else:
        player.rating -= K * wab
        computer.rating += K * wab

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating ratings: {e}")