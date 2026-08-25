from __future__ import annotations

from jupyter_client.provisioning import KernelProvisionerBase


class PublicFixtureProvisioner(KernelProvisionerBase):
    status = None

    @property
    def has_process(self):
        return self.status is None

    async def launch_kernel(self, cmd, **kwargs):
        self.connection_info = dict(kwargs.get("connection_info", {}))
        self.status = None
        return dict(self.connection_info)

    async def poll(self):
        return self.status

    async def wait(self):
        if self.status is None:
            self.status = 0
        return self.status

    async def send_signal(self, signum):
        self.status = int(signum)

    async def kill(self, restart=False):
        self.status = -9

    async def terminate(self, restart=False):
        self.status = 0

    async def cleanup(self, restart=False):
        return None
