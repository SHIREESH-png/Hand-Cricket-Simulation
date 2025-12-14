import tkinter as tk
from tkinter import messagebox
import random
import time

class HandCricketGUI:
    def __init__(self, root):
        self.root = root
        root.title("Hand Cricket")
        root.attributes("-fullscreen", True)

        # Core state
        self.overs = 1
        self.player_name = "You"
        self.computer_name = "Computer"
        self.innings = 0
        self.player_is_batting = True
        self.player_score = 0
        self.comp_score = 0
        self.target = None
        self.balls_left = 6
        self.commentary_lines = [
            "Lovely timing!",
            "What a crisp shot!",
            "That's a risky stroke!",
            "Be careful — that's close!",
            "What a beauty of a ball!",
            "Crowd goes wild!",
            "Hearts racing...",
            "Brilliant running between the wickets!"
        ]
        
        # New animation state variables
        self.current_user_number = None
        self.current_comp_number = None
        self.ball_moving = False
        self.ball_pos = 0

        self.ask_overs()
        self.balls_left = self.overs * 6

        # --- UI LAYOUT ---
        top = tk.Frame(root, pady=8)
        top.pack(fill="x")

        self.score_label = tk.Label(top, text="Player: 0  |  Computer: 0",
                                    font=("Helvetica", 24, "bold"))
        self.score_label.pack(side="left", padx=12)

        self.status_label = tk.Label(top, text="Toss pending", font=("Helvetica", 18))
        self.status_label.pack(side="right", padx=12)

        middle = tk.Frame(root)
        middle.pack(fill="both", expand=True, padx=10, pady=6)

        # LEFT CONTROLS
        left = tk.Frame(middle, bd=1, relief="groove", padx=8, pady=8)
        left.pack(side="left", fill="y")

        tk.Label(left, text="Choose number (1-6)", font=("Arial", 18, "bold")).pack(pady=(0,6))

        self.number_buttons = []
        btn_frame = tk.Frame(left)
        btn_frame.pack()

        for i in range(1, 7):
            b = tk.Button(btn_frame, text=str(i), width=6, height=2, font=("Arial", 18),
                          command=lambda v=i: self.play_ball_by(v))
            b.grid(row=0, column=i-1, padx=6, pady=6)
            self.number_buttons.append(b)

        cfg = tk.Frame(left, pady=10)
        cfg.pack()
        tk.Button(cfg, text="Toss", width=12, height=1,
                  font=("Arial", 16), command=self.open_toss_window).pack(pady=8)
        tk.Button(cfg, text="Reset Game", width=12, height=1,
                  font=("Arial", 16), command=self.reset_game).pack(pady=8)

        tk.Label(cfg, text="(or press keys 1-6)", font=("Arial", 12)).pack()

        # RIGHT COMMENTARY
        right = tk.Frame(middle, bd=1, relief="groove", padx=8, pady=8)
        right.pack(side="left", fill="both", expand=True, padx=(10,0))

        tk.Label(right, text="Commentary", font=("Helvetica", 20, "bold")).pack(anchor="w")

        self.commentary_box = tk.Text(right, width=70, height=25,
                                      state="disabled", wrap="word",
                                      font=("Consolas", 16))
        self.commentary_box.pack(padx=4, pady=6, fill="both", expand=True)

        # BOTTOM FRAME (Balls, Target, and CANVAS for Animation)
        bottom = tk.Frame(root, pady=6)
        bottom.pack(fill="x")

        self.balls_label = tk.Label(bottom, text=f"Balls left: {self.balls_left}",
                                    font=("Helvetica", 18))
        self.balls_label.pack(side="left", padx=12)

        self.target_label = tk.Label(bottom, text="Target: -", font=("Helvetica", 18))
        self.target_label.pack(side="left", padx=18)

        # CANVAS for Animation
        canvas_frame = tk.Frame(bottom, width=400, height=150, bd=1, relief="sunken")
        canvas_frame.pack(side="right", padx=12, pady=4, fill="y")
        canvas_frame.pack_propagate(False)

        self.canvas = tk.Canvas(canvas_frame, bg="#1c4b27", width=400, height=150)
        self.canvas.pack(fill="both", expand=True)

        self._draw_avatars()

        # SAFE CROWD INIT
        self.root.after(200, self._safe_start_crowd)

        # Bind all keypresses and the Escape key for fullscreen
        root.bind_all("<Key>", self._on_keypress)
        root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        self._set_number_buttons_state("disabled")
        self._log("Welcome to Hand Cricket. Select overs and click Toss.")

    # ----------------------------------------------------
    # SAFE CROWD INITIALIZATION
    # ----------------------------------------------------
    def _safe_start_crowd(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w < 100 or h < 50:
            self.root.after(200, self._safe_start_crowd)
            return

        self._draw_avatars(w, h)
        self._init_crowd(w, h)
        self._animate_crowd(w)
        
        # Set up initial animation drawing spots
        self.p_coord_x = w * 0.1 + 15
        self.c_coord_x = w * 0.75 + 20
        self.pitch_y = h * 0.7

    # ----------------------------------------------------
    # DRAW PLAYER, BOWLER & PITCH
    # ----------------------------------------------------
    def _draw_avatars(self, w=None, h=None):
        self.canvas.delete("avatars")

        if w is None or h is None:
            w = 400
            h = 150
            
        # Coordinates for avatars
        p_x = w * 0.1
        c_x = w * 0.75
        y = h * 0.4
        
        # Player (Batter) Avatar - Yellow Circle
        self.canvas.create_oval(p_x, y, p_x+30, y+30,
                                fill="yellow", outline="black", width=2, tags="avatars")
        # Computer (Bowler) Avatar - Orange Rectangle
        self.canvas.create_rectangle(c_x, y-10, c_x+40, y+40,
                                     fill="orange", outline="black", width=2, tags="avatars")
        
        # Simple pitch/ground line
        self.canvas.create_line(0, h*0.7, w, h*0.7, fill="brown", width=3, tags="avatars")

        # The 'ball' element will be created dynamically
        self.ball_item = self.canvas.create_oval(0, 0, 0, 0, fill="red", tags="ball")


    # ----------------------------------------------------
    # CROWD INIT AND ANIMATION
    # ----------------------------------------------------
    def _init_crowd(self, w, h):
        self.crowd_dots = []
        max_y = int(h * 0.3) 
        num_dots = 25 
        
        for i in range(num_dots):
            cx = random.randint(10, w-10)
            cy = random.randint(5, max_y)
            r = random.randint(2,4)
            direction = random.choice([-1, 1])
            color = random.choice(["white", "yellow", "lightblue", "pink"])
            dot = self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="", tags="crowd")
            self.crowd_dots.append([dot, direction])

    def _animate_crowd(self, w):
        for i, (dot, direction) in enumerate(self.crowd_dots):
            self.canvas.move(dot, direction, 0)
            x1, y1, x2, y2 = self.canvas.coords(dot)
            if x1 <= 0 or x2 >= w: 
                direction *= -1
            self.crowd_dots[i][1] = direction
        self.root.after(100, lambda: self._animate_crowd(w))


    # ----------------------------------------------------
    # NEW: MAIN GAME ANIMATION
    # ----------------------------------------------------
    def _update_canvas_display(self, user_num=None, comp_num=None):
        w = self.canvas.winfo_width()
        self.canvas.delete("game_info")

        if user_num is None or comp_num is None:
            # Hide ball and numbers if no ball is played
            self.canvas.coords(self.ball_item, 0, 0, 0, 0)
            return

        # 1. Display Numbers
        is_out = (user_num == comp_num)
        
        p_text_color = "red" if is_out else "white"
        c_text_color = "red" if is_out else "white"

        # Player's Number (Batter or Bowler)
        self.canvas.create_text(self.p_coord_x, self.pitch_y + 15,
                                text=str(user_num), font=("Arial", 20, "bold"),
                                fill=p_text_color, tags="game_info")
        
        # Computer's Number (Bowler or Batter)
        self.canvas.create_text(self.c_coord_x, self.pitch_y + 15,
                                text=str(comp_num), font=("Arial", 20, "bold"),
                                fill=c_text_color, tags="game_info")

        # 2. Start Ball Animation
        self.ball_moving = True
        self.ball_pos = 0 # 0% of the distance
        self._animate_ball()

    def _animate_ball(self):
        if not self.ball_moving:
            return

        w = self.canvas.winfo_width()
        ball_size = 10
        
        # The ball moves from the bowler's spot to the batter's spot
        if self.player_is_batting:
            start_x = self.c_coord_x
            end_x = self.p_coord_x
        else:
            start_x = self.p_coord_x
            end_x = self.c_coord_x
            
        current_x = start_x + (end_x - start_x) * self.ball_pos
        
        self.canvas.coords(self.ball_item, 
                           current_x - ball_size/2, self.pitch_y - ball_size, 
                           current_x + ball_size/2, self.pitch_y)
        
        self.ball_pos += 0.1 # Move 10% of the distance each step

        if self.ball_pos >= 1.0:
            self.ball_moving = False
            # Wait a moment, then hide the ball and numbers
            self.root.after(1000, lambda: self._update_canvas_display(None, None))
        else:
            self.root.after(50, self._animate_ball)


    # ----------------------------------------------------
    # COMMENTARY
    # ----------------------------------------------------
    def _log(self, text):
        self.commentary_box["state"] = "normal"
        self.commentary_box.insert("end", text + "\n")
        self.commentary_box.see("end")
        self.commentary_box["state"] = "disabled"

    # ----------------------------------------------------
    # OVERS SELECTION (UNCHANGED)
    # ----------------------------------------------------
    def ask_overs(self):
        win = tk.Toplevel(self.root)
        win.title("Select Overs")
        win.geometry("400x300")
        win.resizable(False, False)

        tk.Label(win, text="Select Overs", font=("Helvetica", 16, "bold")).pack(pady=20)

        def choose(o):
            self.overs = o
            win.destroy()

        tk.Button(win, text="1 Over", font=("Arial", 16), width=12,
                  command=lambda: choose(1)).pack(pady=5)
        tk.Button(win, text="2 Overs", font=("Arial", 16), width=12,
                  command=lambda: choose(2)).pack(pady=5)
        tk.Button(win, text="5 Overs", font=("Arial", 16), width=12,
                  command=lambda: choose(5)).pack(pady=5)

        win.transient(self.root)
        win.grab_set()
        self.root.wait_window(win)

    # ----------------------------------------------------
    # TOSS (UNCHANGED)
    # ----------------------------------------------------
    def open_toss_window(self):
        if self.innings != 0:
            messagebox.showinfo("Toss", "Toss already done. Reset to play again.")
            return

        toss_win = tk.Toplevel(self.root)
        toss_win.title("Toss")
        toss_win.geometry("350x320")
        toss_win.resizable(False, False)

        tk.Label(toss_win, text="Heads or Tails?", font=("Helvetica", 16)).pack(pady=10)

        choice_var = tk.StringVar(value="heads")
        tk.Radiobutton(toss_win, text="Heads", variable=choice_var, value="heads",
                       font=("Arial", 14)).pack(anchor="w", padx=20)
        tk.Radiobutton(toss_win, text="Tails", variable=choice_var, value="tails",
                       font=("Arial", 14)).pack(anchor="w", padx=20)

        def do_toss():
            landed = random.choice(["heads", "tails"])
            if choice_var.get() == landed:
                self._log(f"You won the toss! ({landed})")
                self._prompt_bat_ball(toss_win)
            else:
                comp_choice = random.choice(["bat", "ball"])
                self.player_is_batting = (comp_choice == "ball")
                self._log(f"Computer won the toss and chooses to {comp_choice}.")
                toss_win.destroy()
                self.start_first_innings()

        tk.Button(toss_win, text="Toss!", font=("Arial", 16),
                  width=10, command=do_toss).pack(pady=12)

        toss_win.transient(self.root)
        toss_win.grab_set()

    def _prompt_bat_ball(self, win):
        tk.Label(win, text="Choose Bat or Ball", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(win, text="Bat", font=("Arial", 14), width=10,
                  command=lambda: self._finish_toss_choice(win, "bat")).pack(pady=5)
        tk.Button(win, text="Ball", font=("Arial", 14), width=10,
                  command=lambda: self._finish_toss_choice(win, "ball")).pack(pady=5)

    def _finish_toss_choice(self, win, choice):
        self.player_is_batting = (choice == "bat")
        self._log(f"You chose to {choice} first.")
        win.destroy()
        self.start_first_innings()

    # ----------------------------------------------------
    # INNINGS START (UNCHANGED)
    # ----------------------------------------------------
    def start_first_innings(self):
        self.player_score = 0
        self.comp_score = 0
        self.balls_left = self.overs * 6
        self.target = None
        self.innings = 1

        who = self.player_name if self.player_is_batting else self.computer_name
        self.status_label.config(text=f"First Innings: {who} batting")

        self._log(f"First innings begins: {who} batting.")
        self._update_ui()
        self._set_number_buttons_state("normal")

    # ----------------------------------------------------
    # GAMEPLAY (UPDATED TO INCLUDE ANIMATION CALL)
    # ----------------------------------------------------
    def play_ball_by(self, user_choice):
        # Prevent double-click/play while animation is running
        if self.ball_moving: 
            return
            
        if self.innings == 0 or self.innings == 3:
            return
        if self._is_buttons_disabled():
            return

        comp_choice = random.randint(1, 6)
        
        # Trigger the visual update *before* processing the score/out
        self._update_canvas_display(user_choice, comp_choice)

        if self.innings == 1:
            self._play_first_innings(user_choice, comp_choice)
            return

        if self.innings == 2:
            self._play_second_innings(user_choice, comp_choice)
            return

    # FIRST INNINGS MODE
    def _play_first_innings(self, user, comp):
        if self.player_is_batting:
            self._log(f"You: {user}  |  Computer bowled {comp}")
            if user == comp:
                self._log("OUT! End of first innings.")
                self.target = self.player_score + 1
                self._log(f"Target for Computer: {self.target}")
                self._start_second_innings()
            else:
                self.player_score += user
                self.balls_left -= 1
                self._maybe_sprinkle_commentary()
        else:
            self._log(f"You bowled {user}  |  Computer played {comp}")
            if user == comp:
                self._log("OUT! Computer all-out.")
                self.target = self.comp_score + 1
                self._log(f"Target for Player: {self.target}")
                self._start_second_innings()
            else:
                self.comp_score += comp
                self.balls_left -= 1
                self._maybe_sprinkle_commentary()

        if self.balls_left == 0 and self.innings == 1:
            if self.player_is_batting:
                self.target = self.player_score + 1
                self._log(f"End of innings. Target for Computer: {self.target}")
            else:
                self.target = self.comp_score + 1
                self._log(f"End of innings. Target for Player: {self.target}")
            self._start_second_innings()

        self._update_ui()

    def _start_second_innings(self):
        self.innings = 2
        self.player_is_batting = not self.player_is_batting
        self.balls_left = self.overs * 6
        who = self.player_name if self.player_is_batting else self.computer_name
        self._log(f"Second innings begins: {who} batting.")

    # SECOND INNINGS MODE
    def _play_second_innings(self, user, comp):
        if self.player_is_batting:
            self._log(f"You: {user}  |  Computer bowled {comp}")
            if user == comp:
                self._log("OUT! Innings over.")
                self._decide_match()
                return
            else:
                self.player_score += user
                self.balls_left -= 1
                self._maybe_sprinkle_commentary()
                if self.player_score >= self.target:
                    self._log(f"You reached the target! You win!")
                    self._end_match()
                    return
        else:
            self._log(f"You bowled {user}  |  Computer played {comp}")
            if user == comp:
                self._log("OUT! Innings over.")
                self._decide_match()
                return
            else:
                self.comp_score += comp
                self.balls_left -= 1
                self._maybe_sprinkle_commentary()
                if self.comp_score >= self.target:
                    self._log("Computer reached the target! Computer wins!")
                    self._end_match()
                    return

        if self.balls_left == 0:
            self._decide_match()
            return

        self._update_ui()

    # MATCH RESULT (UNCHANGED)
    def _decide_match(self):
        if self.player_score > self.comp_score:
            self._log(f"You win by {self.player_score - self.comp_score} runs!")
        elif self.comp_score > self.player_score:
            self._log(f"Computer wins by {self.comp_score - self.player_score} runs!")
        else:
            self._log("Match Tied!")
        self._end_match()

    def _end_match(self):
        self._set_number_buttons_state("disabled")
        self.innings = 3
        msg = f"Final Score\n\nYou: {self.player_score}\nComputer: {self.comp_score}"
        messagebox.showinfo("Match Over", msg)
        self.status_label.config(text="Match finished")

    # HELPERS (UNCHANGED)
    def _maybe_sprinkle_commentary(self):
        if random.random() < 0.45:
            self._log(random.choice(self.commentary_lines))

    def _update_ui(self):
        self.score_label.config(text=f"Player: {self.player_score}  |  Computer: {self.comp_score}")
        self.balls_label.config(text=f"Balls left: {self.balls_left}")
        self.target_label.config(text=f"Target: {self.target if self.target else '-'}")

    def _set_number_buttons_state(self, state):
        for b in self.number_buttons:
            b.config(state=state)

    def _is_buttons_disabled(self):
        return all(b.cget("state") == "disabled" for b in self.number_buttons)

    # KEYBOARD INPUT - CORRECTED TO PREVENT VALUEERROR
    def _on_keypress(self, event):
        # Check if the key character is one of the valid game inputs
        if event.char in "123456":
            # Safely attempt to convert to integer
            try:
                v = int(event.char)
            except ValueError:
                # Should not happen, but serves as a final guard
                return 

            # Only play the ball if the game is active and buttons are enabled
            if self.innings in (1,2) and not self._is_buttons_disabled() and not self.ball_moving:
                self.play_ball_by(v)

    # RESET GAME (UPDATED to clear animation state)
    def reset_game(self):
        self.innings = 0
        self.player_is_batting = True
        self.player_score = 0
        self.comp_score = 0
        self.ask_overs()
        self.balls_left = self.overs * 6
        self.target = None
        self._set_number_buttons_state("disabled")
        self._update_ui()
        self.status_label.config(text="Toss pending")
        
        # Clear animation state
        self.ball_moving = False
        self.canvas.delete("game_info")
        self._update_canvas_display(None, None)

        self.commentary_box["state"] = "normal"
        self.commentary_box.delete("1.0", "end")
        self.commentary_box["state"] = "disabled"
        self._log("Game reset. Select overs and click Toss to start.")


if __name__ == "__main__":
    root = tk.Tk()
    app = HandCricketGUI(root)
    root.mainloop()