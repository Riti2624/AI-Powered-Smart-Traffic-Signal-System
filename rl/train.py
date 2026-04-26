from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from rl.traffic_env import CorridorSignalEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PPO for multi-intersection traffic control")
    parser.add_argument("--timesteps", type=int, default=50000)
    parser.add_argument("--intersections", type=int, default=5)
    parser.add_argument("--output", type=str, default="models/ppo_traffic.zip")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env = DummyVecEnv([lambda: CorridorSignalEnv(intersections=args.intersections)])

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=512,
        batch_size=128,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        ent_coef=0.01,
    )
    model.learn(total_timesteps=args.timesteps)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out))
    print(f"Saved PPO model to {out}")


if __name__ == "__main__":
    main()
