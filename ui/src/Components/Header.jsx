import React from "react";
import { PhacSignature } from "./PhacSignature.tsx";

const Header = () => {
    return (
        <div className="header-wrapper">
            <header className="App-header">
                <PhacSignature language="en" />
            </header>
        </div>
    );
};

export default Header;
