# Cisco SD-WAN Automation

Automation project for the Cisco SD-WAN EVE-NG lab.

## Environment

- vManage: 10.0.200.10
- vSmart: 10.0.200.11
- vBond: 10.0.200.12
- Automation VM: 10.0.200.51

## Software

- Python 3.10
- Ansible 2.17
- Cisco SD-WAN 20.9.1

## Project structure

- `ansible/` — Ansible automation
- `python/` — Python automation and vManage API client

## Goals

1. Automate vManage API authentication
2. Retrieve SD-WAN inventory
3. Bootstrap the SD-WAN control plane
4. Automate device onboarding
5. Automate configuration of remote sites
6. Integrate automation with GitHub

