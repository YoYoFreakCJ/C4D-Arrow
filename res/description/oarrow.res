CONTAINER oarrow
{
	NAME Oarrow;
	INCLUDE Obase;

	GROUP ID_OBJECTPROPERTIES
	{
		LINK OARROW_TARGET              { ACCEPT { Obase; }; }
		REAL OARROW_TARGET_OFFSET       { UNIT METER; }
		REAL OARROW_LENGTH				{ UNIT METER; MIN 0.0; }
		BOOL OARROW_FLAT_ENABLE         { }
		LONG OARROW_ROTATION_SEGMENTS 	{ MIN 3; MAX 100; }
		LONG OARROW_FLAT_ORIENTATION
		{
			CUSTOMGUI QUICKTABRADIO;
			CYCLE
			{
				OARROW_FLAT_ORIENTATION_XP;
				OARROW_FLAT_ORIENTATION_XN;
				OARROW_FLAT_ORIENTATION_YP;
				OARROW_FLAT_ORIENTATION_YN;
				OARROW_FLAT_ORIENTATION_ZP;
				OARROW_FLAT_ORIENTATION_ZN;
			}
		}
	}

	INCLUDE Oprimitiveaxis;

	GROUP OARROW_BASE
	{
		DEFAULT 1;
		REAL OARROW_BASE_RADIUS			{ UNIT METER; MIN 0.0; }
	}

	GROUP OARROW_TIP
	{
		DEFAULT 1;

		REAL OARROW_TIP_RADIUS			{ UNIT METER; MIN 0.0; }
		REAL OARROW_TIP_LENGTH			{ UNIT METER; MIN 0.0; }
	}
}