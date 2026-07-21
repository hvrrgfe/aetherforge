package com.aetherforge.model.component;

public interface Component {
    default String componentType() {
        return getClass().getSimpleName();
    }
}