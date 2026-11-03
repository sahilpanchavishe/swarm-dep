stant_failover_enabled of this CreateBackendSetDetails.
        If enabled existing connections will be forwarded to an alternative healthy backend as soon as current backend becomes unhealthy.


        :return: The is_instant_failover_enabled of this CreateBackendSetDetails.
        :rtype: bool
        """
        return self._is_instant_failover_enabled

    @is_instant_failover_enabled.setter
    def is_instant_failover_enabled(self, is_instant_failover_enabled):
        """
        Sets the is_instant_failover_enabled of this CreateBackendSetDetails.
        If enabled existing connections will be forwarded to an alternative healthy backend as soon as current backend becomes unhealthy.


        :param is_instant_failover_enabled: The is_instant_failover_enabled of this CreateBackendSetDetails.
        :type: bool
        """
        self._is_instant_failover_enabled = is_instant_failover_enabled

    @property
    def is_instant_failover_tcp_reset_enabled(self):
        """
        Gets the is_instant_