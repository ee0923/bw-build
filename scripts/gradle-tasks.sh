#!/usr/bin/env bash
# Shared native and container privacy regressions.
network_tests=(
    :core:testDebugUnitTest
    --tests com.bitwarden.core.util.PrivateServerPolicyTest
    :network:testDebugUnitTest
    --tests com.bitwarden.network.service.HaveIBeenPwnedServiceTest
    --tests com.bitwarden.network.retrofit.RetrofitsTest
    --tests com.bitwarden.network.interceptor.BaseUrlInterceptorTest
    --tests com.bitwarden.network.interceptor.BaseUrlInterceptorsPrivacyTest
    --tests com.bitwarden.network.interceptor.PrivateServerInterceptorTest
    :data:testDebugUnitTest
    --tests com.bitwarden.data.repository.util.PrivateEnvironmentTest
    --tests com.bitwarden.data.repository.util.EnvironmentExtensionsTest
    --tests com.bitwarden.data.repository.util.EnvironmentUrlsDataJsonExtensionsTest
    --tests com.bitwarden.data.manager.flightrecorder.FlightRecorderManagerTest
    --tests com.bitwarden.data.manager.flightrecorder.FlightRecorderWriterPrivacyTest
)
app_tests=(
    :app:testFdroidDebugUnitTest
    --tests com.x8bit.bitwarden.data.platform.manager.sdk.log.SdkLoggerFactoryTest
    --tests com.x8bit.bitwarden.data.platform.repository.SettingsRepositoryTest
    --tests com.x8bit.bitwarden.data.platform.manager.provider.BaseUrlsProviderTest
    --tests com.x8bit.bitwarden.data.platform.manager.sdk.SdkRepositoryFactoryTests
)
