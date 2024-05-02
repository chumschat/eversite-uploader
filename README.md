# Scripts for uploading html-sites to blockchain

It uses [.ever domains](https://app.evername.io/) for storing sites.
Every .ever domain is an NFT-contract with a set of records.
There are two options for storing sites:
1. Store directly in domain NFT-contract (record 1004)
2. Store in separate contract and link it to domain (record 1005)

Scripts are written in Python 3.

## Install dependencies

```shell
python3 -m pip install -r requirements.txt
```

## Prepare the environment

`.env` is used to configure these scripts. 
You should create it like [env_template](.env_template). 
Fill in the fields with your data.

| Field            | Required | Description                                          |
|------------------|----------|------------------------------------------------------|
| `SEED_PHRASE`    | **yes**  | Seed phrase of the wallet that pays for transactions |
| `SITE_ADDRESS`   | **yes**  | Address of the site contract                         |
| `DOMAIN_ADDRESS` | **yes**  | Address of the .ever domain NFT                      |
| `GQL_TRANSPORT`  | no       | Address of GraphQL transport                         |
| `JRPC_TRANSPORT` | no       | Address of JSON-RPC transport                        |

Take in mind that the account of the provided seed phrase has to be the owner of the domain and deployed site.

### Transport

Recommended way is to use GraphQL transport. 
To get the right url of transport you should visit [everclod](https://www.evercloud.dev/), register and create a new project.
Then you will get the url of transport.

You have to specify at least one transport in the environment, so either `GQL_TRANSPORT` or `JRPC_TRANSPORT` should be set.

## Store site directly

This way is strongly limited to store **only 889 bytes**! Use it to store tiny sites or html-formatted text.
Script tries to minify your html before storing, but it does not guarantee that it will fit.
You could use `set_record.py` script for this with the `1004` record key.

```shell
python3 -m set_record -r 1004 sites/my_site.html
```

*Tip* You could store your html in `sites` folder as it is added to `.gitignore`.

## Upload site to special contract

### 1. Deploy site contract

You could deploy [site contract from special repository](https://github.com/chumschat/eversite-contract).
You will get the contract address and use it in the next steps.

### 2. Upload site

After deploying the site contract you could upload html to it.
You could use `upload_site.py` script for this. 
This script also tries to minify your html.

```shell
python3 -m upload_site sites/my_site.html
```

*Tip* You could store your html in `sites` folder as it is added to `.gitignore`.

### 3. Link domain to site

After uploading the site you should link it to the domain.
You could use `set_record.py` script for this with the `1005` record key (default).

```shell
python3 -m set_record -r 1005
```

## Troubleshooting

### RuntimeError: Message expired

If you can't upload a site with constantly error `RuntimeError: Message expired`,
and your transaction is not accepted, that often means that the contract hasn't enough gas on its balance.

Script `upload_site.py` uses external messages to send data to the contract. 
It is the cheapest way to send *large* amount of data to the contract.
Such messages come without gas, so it is consumed from the site contract.
Script divides html into chunks of 60&nbsp;000 symbols, you could see it in the logs.
Each of such chunk requires about 0.27-0.3 EVER for gas that should be on the contract balance.
I.e. for 5 chunks you should have about 1.5 EVER on the contract balance.

### Shrink amount of chunks

Currently, if you upload a site with multiple chunks, you wouldn't be able to upload it again with the smaller number of chinks.
Old high-indexed chunks will stay in the contract, and it's overall content will be corrupted.
You cannot do anything without it. You could only destroy old site using it's `destruct` method and redeploy new contract.
By doing this you could at least get the remaining gas back.

Consider onchain sites as immutable.
