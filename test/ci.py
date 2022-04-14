import json
import os.path as op
import sys
sys.path.append(op.dirname(op.dirname(op.abspath(__file__))))

from oecp.utils.shell import shell_cmd

def real_plan(plan):
	if plan.startswith('/'):
		return plan
	
	return op.join(op.dirname(op.dirname(op.abspath(__file__))), "oecp", "conf", "plan", plan)

def run_ci():
	ci_config_file = op.join(op.dirname(op.abspath(__file__)), "ci.json")
	cli_file = op.join(op.dirname(op.dirname(op.abspath(__file__))), "cli.py")
	root_dir = op.dirname(op.dirname(op.abspath(__file__)))
	print(root_dir)
	with open(ci_config_file, 'r') as fp:
		ci_config = json.load(fp) 
		certs = ci_config.get("certs")
		for item in certs:
			base = item.get("base")
			cert = item.get("cert")
			plan = real_plan(item.get("plan", "all.json"))
			cmd = "python3 {} {} {} -p {} -o {}".format(cli_file, base, cert, plan, root_dir)
			print(cmd)
			ret, out, err = shell_cmd(cmd.split())
			print(ret)
			print(out)
			print(err)
	if err:
		exit(1)

if __name__ == "__main__":
	run_ci()
