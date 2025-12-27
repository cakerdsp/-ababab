extends CharacterBody2D


const a = 12.5
const a_ = 300.0
const SPEED = 300.0
const JUMP_VELOCITY = -400.0
const SPRINT = 2000.0
var towards = 1
var is_sprint = 0


const combo := {
	"1_1_1_2": [2,0]
}
const combo_checker := {
	"1_1_1_2": 500
}
# 攻击需要判断的动作组
const Enum_attack := {  
	"idle": 0,
	"jump": 1,  
	"left_right": 2,
	"right_right": 3,
	"right_left": 4,
	"left_left": 5
}  
# 方便代码编写所维护的Enum_attack的翻转表
const Enum_attack_reverse := {  
	0: "idle",
	1: "jump",  
	2: "left_right",
	3: "right_right",
	4: "right_left",
	5: "left_left"
}  

# 存储所有攻击动作组的检查时间间隔(以攻击作为结束)
const Enum_attack_checker := {  
	"attack1": 1500,
	"attack2": 1500,
	"jump": 500,  
	"left_right": 500,
	"right_right": 500,
	"right_left": 500,
	"left_left": 500
}  

# 存储以右移结束的动作组的时间戳
var time_right := {   
	"left_right": 0,
	"right_right": 0
}  
# 存储以左移结束的动作组的时间戳
var time_left := {   
	"right_left": 0,
	"left_left": 0
}  

# 存储所有移动动作组的检查时间间隔
const time_press_checker := {   
	"left_right": 500,
	"right_right": 500,
	"right_left": 500,
	"left_left": 500
} 

# 存储以跳跃结束的动作组的时间戳
var time_jump := {
	"time_jump": 0
}


# 存储攻击的最新需要判断的状态，以及最新的更新时间
var attack_stack = Enum_attack["idle"]
var time_attack = 0

# 攻击1有4段，攻击2有3段
const ATTACK1_COUNT = 4
const ATTACK2_COUNT = 3
# -1保证下一次攻击一定从0开始
var attack1_counter = -1
var time_attack1 = 0
var attack2_counter = -1
var time_attack2 = 0

func _ready() -> void:
	pass



func _process(delta: float) -> void: 
	# 利用翻转表获取动作组名称
	var act = Enum_attack_reverse[attack_stack]
	if attack_stack != Enum_attack["idle"] and Time.get_ticks_msec() - time_attack >= Enum_attack_checker[act]:
		attack_stack = Enum_attack["idle"]
	# attack1与attack2不能共存
	if Input.is_action_just_pressed("attack1"):
		# 计算当前应该是第几连段
		if Time.get_ticks_msec() - time_attack1 < Enum_attack_checker["attack1"]:
			attack1_counter = (attack1_counter + 1) % ATTACK1_COUNT
		else:
			attack1_counter = 0
		# 如果状态不是空闲，证明有需要判断的动作组，且通过时间检查
		if attack_stack != Enum_attack["idle"]:
			print(act + "_attack1")
			# 重置攻击1连段,-1保证下一次攻击一定从0开始
			attack1_counter = -1
		elif [attack1_counter,attack2_counter] in combo.values():
			print("combo")
			attack1_counter = -1
			attack2_counter = -1
		else:
			print("attack1_" + str(attack1_counter))
			
		# 状态置为空闲,防止出现重复触发
		attack_stack = Enum_attack["idle"]
		# 更新攻击1连段时间
		time_attack1 = 	Time.get_ticks_msec()
		
		
	elif Input.is_action_just_pressed("attack2"):
		# 计算当前应该是第几连段
		if Time.get_ticks_msec() - time_attack2 < Enum_attack_checker["attack2"]:
			attack2_counter = (attack2_counter + 1) % ATTACK2_COUNT
		else:
			attack2_counter = 0
		# 如果状态非空闲且通过时间检查
		if attack_stack != Enum_attack["idle"]:
			print(act + "_attack2")
			# 重置攻击2连段,-1保证下一次攻击一定从0开始
			attack2_counter = -1
			
		elif [attack1_counter,attack2_counter] in combo.values():
			var c = combo.find_key([attack1_counter,attack2_counter])
			print("combo")
			attack1_counter = -1
			attack2_counter = -1
		else:
			print("attack2_" + str(attack2_counter))
		# 更新攻击2连段时间
		
		# 状态置为空闲
		attack_stack = Enum_attack["idle"]
		# 更新攻击2连段时间
		time_attack2 = 	Time.get_ticks_msec()
		
		
	if Input.is_action_just_pressed("jump"):
		time_attack = Time.get_ticks_msec()
		attack_stack = Enum_attack["jump"]
		
		# 更新和跳跃有关的动作的时间戳
		time_jump["jump"] = Time.get_ticks_msec()
		
	if Input.is_action_just_pressed("left"):
		# 首先获取时间最近的键
		var tmp_ = time_left.find_key(time_left.values().max())
		# 判断是否通过检查
		if Time.get_ticks_msec() - time_left[tmp_] < time_press_checker[tmp_]:
			time_attack = Time.get_ticks_msec()
			attack_stack = Enum_attack[tmp_]
			
		# 更新和左移有关的动作的时间戳
		time_left["left_left"] = Time.get_ticks_msec()
		time_right["left_right"] = Time.get_ticks_msec()
			
	if Input.is_action_just_pressed("right"):
		# 首先获取时间最近的键
		var tmp_ = time_right.find_key(time_right.values().max())
		# 判断是否通过检查
		if Time.get_ticks_msec() - time_right[tmp_] < time_press_checker[tmp_]:
			time_attack = Time.get_ticks_msec()
			attack_stack = Enum_attack[tmp_]
			
		# 更新和右移有关的动作的时间戳
		time_right["right_right"] = Time.get_ticks_msec()
		time_left["right_left"] = Time.get_ticks_msec()
			
		
		
func _physics_process(delta: float) -> void:
	# Add the gravity.
	if not is_on_floor():
		velocity += get_gravity() * delta

	# Handle jump.
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Get the input direction and handle the movement/deceleration.
	# As good practice, you should replace UI actions with custom gameplay actions.
	var direction := Input.get_axis("left", "right")
	# 如果移动了方向键
	if direction:
		towards = direction
		if not is_sprint:
			velocity.x = move_toward(velocity.x, direction * SPEED, a)
			
	# 对于减速情况的判断
	if not direction or is_sprint:
		# 否则速度以SPEED衰减，这样可能会导致没有惯性，修改后面的值可以创造出惯性的效果
		velocity.x = move_toward(velocity.x, 0, a_)
		if absf(velocity.x) == 0:
			is_sprint = 0
	
	if Input.is_action_just_pressed("sprint") and not is_sprint:
		velocity.x = towards * SPRINT
		is_sprint = 1
		
	# print(velocity.x)
	move_and_slide()
