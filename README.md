# Interoperable Immunization Data Initiative (IIDI)

## One-liner summary

TODO

## Development quickstart

Prerequisites:

- Node v22 (v18 may be sufficient)
- Docker v27 (older versions may be sufficient, unverified)
- VSCode (not strictly required, other editors could be used, but assumed in future steps)

Quickstart:

- Clone repository locally
- Run `npm run ci:all` in the repo root, to install all project and service dependencies
- Install recommended vscode exstensions (see `.vscode/extensions.json`)
- Start the local dev docker-compose environment with `npm run dev` from the repo root

At this point, all services should be available on `localhost`, at the ports configured in `dev_docker_env/docker-compose.dev.yaml`. Services running in the docker-compose envrionment will reboot/rebuild/reinstal when changes are made to their corresponding `.env.dev-public`, `package-lock.json` and `src` files on your local filesystem, to provide a live-development experience. Restarting the docker-compose environment will clear any persistent data, and should only be necessary when that is desired (TODO: specifics on this are pending whether we actually have any persistent components).

To run with node debuggers attached, use `npm run dev:debug` (TODO: this and other variations are pending the specifics of our service architecture).
